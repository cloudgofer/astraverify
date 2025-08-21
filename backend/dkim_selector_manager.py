import os
import logging
import re
import dns.resolver
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from firestore_config import firestore_manager

logger = logging.getLogger(__name__)

class DKIMSelectorManager:
    """
    Advanced DKIM Selector Management System
    
    Features:
    - Admin-managed selectors per domain
    - Discovered selectors from email analysis
    - Brute force selector checking with intelligent ordering
    - Editable brute force selector lists
    - Performance tracking and analytics
    """
    
    def __init__(self):
        self.environment = os.environ.get('ENVIRONMENT', 'local')
        self.brute_force_selectors = self._load_brute_force_selectors()
        self.max_selectors_per_scan = 15  # Limit for performance
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour cache
        
    def _load_brute_force_selectors(self) -> List[str]:
        """Load brute force selectors from file"""
        try:
            with open('resources/dkim_selectors.txt', 'r') as f:
                selectors = [line.strip() for line in f if line.strip()]
            logger.info(f"Loaded {len(selectors)} brute force selectors")
            return selectors
        except FileNotFoundError:
            logger.warning("dkim_selectors.txt not found, using default selectors")
            return ['default', 'google', 'selector1', 'selector2', 'k1', 'dkim1']
    
    def _save_brute_force_selectors(self, selectors: List[str]) -> bool:
        """Save brute force selectors to file"""
        try:
            with open('resources/dkim_selectors.txt', 'w') as f:
                for selector in selectors:
                    f.write(f"{selector}\n")
            self.brute_force_selectors = selectors
            logger.info(f"Saved {len(selectors)} brute force selectors")
            return True
        except Exception as e:
            logger.error(f"Failed to save brute force selectors: {e}")
            return False
    
    def get_domain_selectors(self, domain: str, custom_selector: Optional[str] = None) -> Dict[str, Any]:
        """
        Get comprehensive selector list for a domain with intelligent ordering
        
        Priority order:
        1. Custom selector (if provided)
        2. Admin-managed selectors (high priority first)
        3. Discovered selectors (verified)
        4. Brute force selectors (intelligent subset)
        """
        # Get admin-managed selectors
        admin_selectors = self._get_admin_selectors(domain)
        
        # Get discovered selectors
        discovered_selectors = self._get_discovered_selectors(domain)
        
        # Build priority-ordered list
        selector_list = []
        
        # 1. Custom selector (highest priority)
        if custom_selector:
            selector_list.append({
                'selector': custom_selector,
                'source': 'custom',
                'priority': 1,
                'verified': False
            })
        
        # 2. Admin-managed selectors (by priority)
        for selector_data in admin_selectors:
            priority_map = {'high': 2, 'medium': 3, 'low': 4}
            selector_list.append({
                'selector': selector_data['selector'],
                'source': 'admin',
                'priority': priority_map.get(selector_data.get('priority', 'medium'), 3),
                'verified': selector_data.get('verification_status') == 'verified',
                'admin_data': selector_data
            })
        
        # 3. Discovered selectors (verified)
        for selector_data in discovered_selectors:
            if selector_data.get('verification_status') == 'verified':
                selector_list.append({
                    'selector': selector_data['selector'],
                    'source': 'discovered',
                    'priority': 5,
                    'verified': True,
                    'discovery_data': selector_data
                })
        
        # 4. Brute force selectors (intelligent subset)
        brute_force_subset = self._get_intelligent_brute_force_subset(domain)
        for selector in brute_force_subset:
            selector_list.append({
                'selector': selector,
                'source': 'brute_force',
                'priority': 6,
                'verified': False
            })
        
        # Sort by priority and remove duplicates
        unique_selectors = []
        seen = set()
        for item in sorted(selector_list, key=lambda x: x['priority']):
            if item['selector'] not in seen:
                unique_selectors.append(item)
                seen.add(item['selector'])
        
        # Limit for performance
        final_selectors = unique_selectors[:self.max_selectors_per_scan]
        
        return {
            'domain': domain,
            'selectors': final_selectors,
            'total_available': len(unique_selectors),
            'total_used': len(final_selectors),
            'sources': {
                'custom': len([s for s in final_selectors if s['source'] == 'custom']),
                'admin': len([s for s in final_selectors if s['source'] == 'admin']),
                'discovered': len([s for s in final_selectors if s['source'] == 'discovered']),
                'brute_force': len([s for s in final_selectors if s['source'] == 'brute_force'])
            }
        }
    
    def _get_admin_selectors(self, domain: str) -> List[Dict[str, Any]]:
        """Get admin-managed selectors for a domain"""
        try:
            db = firestore_manager._get_client()
            if not db:
                return []
            
            # Use environment-specific collection
            collection_name = 'dkim_selectors'
            if self.environment == 'staging':
                collection_name = 'dkim_selectors_staging'
            elif self.environment == 'local':
                collection_name = 'dkim_selectors_local'
            
            doc_ref = db.collection(collection_name).document(domain)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                return data.get('admin_selectors', [])
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get admin selectors for {domain}: {e}")
            return []
    
    def _get_discovered_selectors(self, domain: str) -> List[Dict[str, Any]]:
        """Get discovered selectors for a domain"""
        try:
            db = firestore_manager._get_client()
            if not db:
                return []
            
            # Use environment-specific collection
            collection_name = 'dkim_selectors'
            if self.environment == 'staging':
                collection_name = 'dkim_selectors_staging'
            elif self.environment == 'local':
                collection_name = 'dkim_selectors_local'
            
            doc_ref = db.collection(collection_name).document(domain)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                return data.get('discovered_selectors', [])
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get discovered selectors for {domain}: {e}")
            return []
    
    def _get_intelligent_brute_force_subset(self, domain: str) -> List[str]:
        """Get intelligent subset of brute force selectors based on domain patterns"""
        # Start with most common selectors
        common_selectors = ['default', 'google', 'selector1', 'selector2', 'k1', 'dkim1']
        
        # Add provider-specific selectors based on domain patterns
        provider_selectors = self._get_provider_specific_selectors(domain)
        
        # Add remaining selectors (limit to avoid performance issues)
        remaining_selectors = [s for s in self.brute_force_selectors 
                             if s not in common_selectors and s not in provider_selectors]
        
        # Combine and limit
        all_selectors = common_selectors + provider_selectors + remaining_selectors
        return all_selectors[:10]  # Limit to 10 brute force selectors
    
    def _get_provider_specific_selectors(self, domain: str) -> List[str]:
        """Get provider-specific selectors based on domain patterns"""
        # This could be enhanced with ML-based provider detection
        provider_patterns = {
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
        
        # For now, return common selectors
        # This could be enhanced with domain analysis
        return ['google', 'selector1', 'selector2']
    
    def add_admin_selector(self, domain: str, selector: str, notes: str = '', 
                          priority: str = 'medium', added_by: str = 'system') -> bool:
        """Add admin-managed selector for a domain"""
        try:
            # Validate selector format
            if not re.match(r'^[a-zA-Z0-9_-]+$', selector):
                logger.error(f"Invalid selector format: {selector}")
                return False
            
            # Test selector before adding
            test_result = self._test_selector(domain, selector)
            
            db = firestore_manager._get_client()
            if not db:
                return False
            
            # Use environment-specific collection
            collection_name = 'dkim_selectors'
            if self.environment == 'staging':
                collection_name = 'dkim_selectors_staging'
            elif self.environment == 'local':
                collection_name = 'dkim_selectors_local'
            
            doc_ref = db.collection(collection_name).document(domain)
            
            # Get existing data
            doc = doc_ref.get()
            if doc.exists:
                data = doc.to_dict()
                admin_selectors = data.get('admin_selectors', [])
            else:
                data = {}
                admin_selectors = []
            
            # Check if selector already exists
            for existing in admin_selectors:
                if existing['selector'] == selector:
                    logger.warning(f"Selector {selector} already exists for {domain}")
                    return False
            
            # Add new selector
            new_selector = {
                'selector': selector,
                'added_by': added_by,
                'added_date': datetime.utcnow(),
                'notes': notes,
                'priority': priority,
                'status': 'active',
                'verification_status': 'verified' if test_result['valid'] else 'failed',
                'last_tested': datetime.utcnow(),
                'test_results': test_result
            }
            
            admin_selectors.append(new_selector)
            
            # Update document
            data['admin_selectors'] = admin_selectors
            data['last_updated'] = datetime.utcnow()
            
            doc_ref.set(data, merge=True)
            
            logger.info(f"Added admin selector {selector} for {domain}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add admin selector {selector} for {domain}: {e}")
            return False
    
    def remove_admin_selector(self, domain: str, selector: str) -> bool:
        """Remove admin-managed selector for a domain"""
        try:
            db = firestore_manager._get_client()
            if not db:
                return False
            
            # Use environment-specific collection
            collection_name = 'dkim_selectors'
            if self.environment == 'staging':
                collection_name = 'dkim_selectors_staging'
            elif self.environment == 'local':
                collection_name = 'dkim_selectors_local'
            
            doc_ref = db.collection(collection_name).document(domain)
            doc = doc_ref.get()
            
            if not doc.exists:
                return False
            
            data = doc.to_dict()
            admin_selectors = data.get('admin_selectors', [])
            
            # Remove selector
            admin_selectors = [s for s in admin_selectors if s['selector'] != selector]
            
            # Update document
            data['admin_selectors'] = admin_selectors
            data['last_updated'] = datetime.utcnow()
            
            doc_ref.set(data, merge=True)
            
            logger.info(f"Removed admin selector {selector} for {domain}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove admin selector {selector} for {domain}: {e}")
            return False
    
    def add_discovered_selector(self, domain: str, selector: str, source: str = 'email_analysis',
                               verification_status: str = 'unverified') -> bool:
        """Add discovered selector for a domain"""
        try:
            db = firestore_manager._get_client()
            if not db:
                return False
            
            # Use environment-specific collection
            collection_name = 'dkim_selectors'
            if self.environment == 'staging':
                collection_name = 'dkim_selectors_staging'
            elif self.environment == 'local':
                collection_name = 'dkim_selectors_local'
            
            doc_ref = db.collection(collection_name).document(domain)
            
            # Get existing data
            doc = doc_ref.get()
            if doc.exists:
                data = doc.to_dict()
                discovered_selectors = data.get('discovered_selectors', [])
            else:
                data = {}
                discovered_selectors = []
            
            # Check if selector already exists
            for existing in discovered_selectors:
                if existing['selector'] == selector:
                    # Update existing selector
                    existing['usage_count'] = existing.get('usage_count', 0) + 1
                    existing['last_used'] = datetime.utcnow()
                    existing['verification_status'] = verification_status
                    break
            else:
                # Add new selector
                new_selector = {
                    'selector': selector,
                    'source': source,
                    'discovery_date': datetime.utcnow(),
                    'usage_count': 1,
                    'verification_status': verification_status,
                    'last_used': datetime.utcnow()
                }
                discovered_selectors.append(new_selector)
            
            # Update document
            data['discovered_selectors'] = discovered_selectors
            data['last_updated'] = datetime.utcnow()
            
            doc_ref.set(data, merge=True)
            
            logger.info(f"Added/updated discovered selector {selector} for {domain}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add discovered selector {selector} for {domain}: {e}")
            return False
    
    def _test_selector(self, domain: str, selector: str) -> Dict[str, Any]:
        """Test a DKIM selector"""
        try:
            dkim_domain = f"{selector}._domainkey.{domain}"
            records = dns.resolver.resolve(dkim_domain, 'TXT')
            
            for record in records:
                record_text = record.to_text().strip('"')
                if record_text.startswith('v=DKIM1'):
                    return {
                        'valid': True,
                        'dns_found': True,
                        'valid_format': True,
                        'record_preview': record_text[:100] + '...' if len(record_text) > 100 else record_text,
                        'full_record': record_text
                    }
            
            return {
                'valid': False,
                'dns_found': True,
                'valid_format': False,
                'error': 'No valid DKIM record found'
            }
            
        except dns.resolver.NXDOMAIN:
            return {
                'valid': False,
                'dns_found': False,
                'valid_format': False,
                'error': 'DNS record not found'
            }
        except Exception as e:
            return {
                'valid': False,
                'dns_found': False,
                'valid_format': False,
                'error': str(e)
            }
    
    def get_brute_force_selectors(self) -> List[str]:
        """Get current brute force selectors"""
        return self.brute_force_selectors.copy()
    
    def update_brute_force_selectors(self, selectors: List[str]) -> bool:
        """Update brute force selectors"""
        return self._save_brute_force_selectors(selectors)
    
    def get_domain_selector_summary(self, domain: str) -> Dict[str, Any]:
        """Get comprehensive selector summary for a domain"""
        admin_selectors = self._get_admin_selectors(domain)
        discovered_selectors = self._get_discovered_selectors(domain)
        
        return {
            'domain': domain,
            'admin_selectors': {
                'total': len(admin_selectors),
                'active': len([s for s in admin_selectors if s.get('status') == 'active']),
                'verified': len([s for s in admin_selectors if s.get('verification_status') == 'verified']),
                'selectors': admin_selectors
            },
            'discovered_selectors': {
                'total': len(discovered_selectors),
                'verified': len([s for s in discovered_selectors if s.get('verification_status') == 'verified']),
                'total_usage': sum(s.get('usage_count', 0) for s in discovered_selectors),
                'selectors': discovered_selectors
            },
            'brute_force_selectors': {
                'total': len(self.brute_force_selectors),
                'sample': self.brute_force_selectors[:10]
            }
        }

# Global instance
dkim_selector_manager = DKIMSelectorManager()
