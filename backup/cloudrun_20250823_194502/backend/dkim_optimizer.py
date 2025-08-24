import asyncio
import aiodns
import dns.resolver
from typing import List, Dict, Any, Optional
import logging
from concurrent.futures import ThreadPoolExecutor
import time

logger = logging.getLogger(__name__)

class DKIMOptimizer:
    def __init__(self):
        self.resolver = aiodns.DNSResolver()
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes cache
        
    def _load_selectors(self) -> List[str]:
        """Load DKIM selectors from file with smart prioritization"""
        try:
            with open('resources/dkim_selectors.txt', 'r') as f:
                all_selectors = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            # Fallback to common selectors
            all_selectors = ['default', 'google', 'k1', 'selector1', 'selector2', 'dreamhost', 'mailgun', 'sendgrid', 'zoho', 'yahoo']
        
        # Prioritize most common selectors first
        priority_selectors = [
            'default', 'google', 'google1', 'google2', 'google2025',
            'selector1', 'selector2', 'k1', 'k2',
            'mailgun', 'mg', 'sendgrid', 'sg',
            'zoho', 'zohomail', 'yahoo', 'ya',
            'dreamhost', 'mailchimp', 'mc', 'hubspot', 'hs'
        ]
        
        # Create optimized selector list: priority first, then others
        optimized_selectors = []
        seen = set()
        
        # Add priority selectors first
        for selector in priority_selectors:
            if selector in all_selectors and selector not in seen:
                optimized_selectors.append(selector)
                seen.add(selector)
        
        # Add remaining selectors (limit to first 50 for performance)
        remaining = [s for s in all_selectors if s not in seen][:50]
        optimized_selectors.extend(remaining)
        
        return optimized_selectors
    
    def _get_provider_specific_selectors(self, mx_servers: List[str]) -> List[str]:
        """Get selectors specific to detected email provider"""
        mx_lower = [server.lower() for server in mx_servers]
        
        provider_selectors = {
            'google': ['google', 'google1', 'google2', 'google2025', 'gapps'],
            'microsoft': ['selector1', 'selector2', 's1', 's2', 'o365s1', 'o365s2'],
            'yahoo': ['yahoo', 'ya'],
            'zoho': ['zoho', 'zohomail'],
            'mailgun': ['mailgun', 'mg'],
            'sendgrid': ['sendgrid', 'sg'],
            'dreamhost': ['dreamhost'],
            'mailchimp': ['mailchimp', 'mc'],
            'hubspot': ['hubspot', 'hs'],
            'salesforce': ['salesforce'],
            'amazon': ['amazonses', 'ses']
        }
        
        for provider, selectors in provider_selectors.items():
            if any(provider in server for server in mx_lower):
                return selectors
        
        return []
    
    async def _check_selector_async(self, domain: str, selector: str) -> Optional[Dict[str, Any]]:
        """Check a single DKIM selector asynchronously"""
        try:
            dkim_domain = f"{selector}._domainkey.{domain}"
            records = await self.resolver.query(dkim_domain, 'TXT')
            
            for record in records:
                record_text = record.text.strip('"')
                if record_text.startswith('v=DKIM1'):
                    return {
                        'selector': selector,
                        'record': record_text[:100] + '...' if len(record_text) > 100 else record_text,
                        'valid': True,
                        'full_record': record_text
                    }
        except Exception as e:
            # Log only if it's not a NXDOMAIN error (which is expected)
            if 'NXDOMAIN' not in str(e):
                logger.debug(f"Error checking selector {selector} for {domain}: {e}")
        
        return None
    
    async def _check_selectors_batch(self, domain: str, selectors: List[str], max_concurrent: int = 10) -> List[Dict[str, Any]]:
        """Check multiple selectors in parallel with concurrency limit"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def check_with_semaphore(selector):
            async with semaphore:
                return await self._check_selector_async(domain, selector)
        
        tasks = [check_with_semaphore(selector) for selector in selectors]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None results and exceptions
        valid_results = []
        for result in results:
            if isinstance(result, dict) and result is not None:
                valid_results.append(result)
        
        return valid_results
    
    def _get_cached_result(self, domain: str) -> Optional[Dict[str, Any]]:
        """Get cached result if available and not expired"""
        if domain in self.cache:
            cached_time, cached_result = self.cache[domain]
            if time.time() - cached_time < self.cache_ttl:
                return cached_result
            else:
                del self.cache[domain]
        return None
    
    def _cache_result(self, domain: str, result: Dict[str, Any]):
        """Cache the result for future use"""
        self.cache[domain] = (time.time(), result)
    
    async def get_dkim_details_optimized(self, domain: str, custom_selector: Optional[str] = None, mx_servers: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get DKIM details with optimized performance"""
        start_time = time.time()
        
        # Check cache first
        cached_result = self._get_cached_result(domain)
        if cached_result:
            logger.info(f"DKIM cache hit for {domain}")
            return cached_result
        
        # Load and prioritize selectors
        all_selectors = self._load_selectors()
        
        # Add custom selector if provided
        if custom_selector and custom_selector not in all_selectors:
            all_selectors.insert(0, custom_selector)
        
        # Get provider-specific selectors if MX servers are provided
        provider_selectors = []
        if mx_servers:
            provider_selectors = self._get_provider_specific_selectors(mx_servers)
            # Add provider selectors to the beginning
            for selector in reversed(provider_selectors):
                if selector in all_selectors:
                    all_selectors.remove(selector)
                    all_selectors.insert(0, selector)
        
        # Limit selectors for performance (check most likely ones first)
        selectors_to_check = all_selectors[:30]  # Check first 30 selectors
        
        logger.info(f"Checking {len(selectors_to_check)} DKIM selectors for {domain}")
        
        # Check selectors in parallel
        dkim_records = await self._check_selectors_batch(domain, selectors_to_check)
        
        # If no records found in first batch, check remaining selectors (but limit to 50 more)
        if not dkim_records and len(all_selectors) > 30:
            remaining_selectors = all_selectors[30:80]  # Check 50 more selectors
            logger.info(f"No DKIM found in first batch, checking {len(remaining_selectors)} more selectors")
            additional_records = await self._check_selectors_batch(domain, remaining_selectors)
            dkim_records.extend(additional_records)
            selectors_to_check.extend(remaining_selectors)
        
        # Prepare result
        if dkim_records:
            result = {
                'has_dkim': True,
                'records': dkim_records,
                'status': 'Valid',
                'description': f'Found {len(dkim_records)} DKIM record(s)',
                'selectors_checked': len(selectors_to_check),
                'check_time': time.time() - start_time
            }
        else:
            result = {
                'has_dkim': False,
                'records': [],
                'status': 'Not Found',
                'description': f'No DKIM records found (checked {len(selectors_to_check)} selectors)',
                'selectors_checked': len(selectors_to_check),
                'check_time': time.time() - start_time
            }
        
        # Cache the result
        self._cache_result(domain, result)
        
        logger.info(f"DKIM check completed for {domain} in {result['check_time']:.2f}s")
        return result
    
    def get_dkim_details_sync(self, domain: str, custom_selector: Optional[str] = None, mx_servers: Optional[List[str]] = None) -> Dict[str, Any]:
        """Synchronous wrapper for the async DKIM checker"""
        try:
            # Check if we're already in an event loop
            loop = asyncio.get_running_loop()
            # If we're in an event loop, we need to create a task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.get_dkim_details_optimized(domain, custom_selector, mx_servers))
                return future.result()
        except RuntimeError:
            # No event loop running, we can use asyncio.run
            return asyncio.run(
                self.get_dkim_details_optimized(domain, custom_selector, mx_servers)
            )

# Global instance for reuse
dkim_optimizer = DKIMOptimizer()
