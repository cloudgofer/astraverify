import dns.resolver
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dkim_selector_manager import dkim_selector_manager

logger = logging.getLogger(__name__)

class EnhancedDKIMScanner:
    """
    Enhanced DKIM Scanner with intelligent selector management
    
    Features:
    - Uses admin-managed selectors
    - Incorporates discovered selectors
    - Intelligent brute force checking
    - Performance optimization
    - Detailed analytics
    """
    
    def __init__(self):
        self.max_parallel_checks = 5  # Limit concurrent DNS queries
        self.timeout = 5  # DNS query timeout in seconds
        
    def scan_domain_dkim(self, domain: str, custom_selector: Optional[str] = None) -> Dict[str, Any]:
        """
        Comprehensive DKIM scan for a domain using all available selectors
        
        Returns detailed analysis including:
        - All found DKIM records
        - Selector sources and priorities
        - Performance metrics
        - Recommendations
        """
        start_time = datetime.utcnow()
        
        # Get comprehensive selector list
        selector_data = dkim_selector_manager.get_domain_selectors(domain, custom_selector)
        
        # Scan all selectors
        scan_results = self._scan_selectors(domain, selector_data['selectors'])
        
        # Process results
        found_records = []
        failed_selectors = []
        
        for result in scan_results:
            if result['found']:
                found_records.append(result)
            else:
                failed_selectors.append(result)
        
        # Calculate performance metrics
        scan_duration = (datetime.utcnow() - start_time).total_seconds()
        
        # Generate recommendations
        recommendations = self._generate_recommendations(found_records, failed_selectors, selector_data)
        
        # Store discovered selectors
        self._store_discovered_selectors(domain, found_records)
        
        return {
            'domain': domain,
            'scan_timestamp': start_time,
            'scan_duration_seconds': scan_duration,
            'has_dkim': len(found_records) > 0,
            'records': found_records,
            'failed_selectors': failed_selectors,
            'selector_analytics': {
                'total_checked': len(selector_data['selectors']),
                'total_found': len(found_records),
                'success_rate': len(found_records) / len(selector_data['selectors']) if selector_data['selectors'] else 0,
                'sources': selector_data['sources'],
                'performance': {
                    'selectors_per_second': len(selector_data['selectors']) / scan_duration if scan_duration > 0 else 0,
                    'average_response_time': scan_duration / len(selector_data['selectors']) if selector_data['selectors'] else 0
                }
            },
            'recommendations': recommendations,
            'status': 'Valid' if found_records else 'Not Found',
            'description': self._generate_description(found_records, selector_data)
        }
    
    def _scan_selectors(self, domain: str, selectors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Scan multiple selectors with performance optimization"""
        results = []
        
        for selector_info in selectors:
            selector = selector_info['selector']
            source = selector_info['source']
            priority = selector_info['priority']
            
            try:
                # DNS query with timeout
                dkim_domain = f"{selector}._domainkey.{domain}"
                records = dns.resolver.resolve(dkim_domain, 'TXT', timeout=self.timeout)
                
                for record in records:
                    record_text = record.to_text().strip('"')
                    if record_text.startswith('v=DKIM1'):
                        results.append({
                            'selector': selector,
                            'source': source,
                            'priority': priority,
                            'found': True,
                            'record': record_text,
                            'record_preview': record_text[:100] + '...' if len(record_text) > 100 else record_text,
                            'valid': True,
                            'error': None,
                            'scan_time': datetime.utcnow()
                        })
                        break
                else:
                    # No valid DKIM record found
                    results.append({
                        'selector': selector,
                        'source': source,
                        'priority': priority,
                        'found': False,
                        'record': None,
                        'record_preview': None,
                        'valid': False,
                        'error': 'No valid DKIM record found',
                        'scan_time': datetime.utcnow()
                    })
                    
            except dns.resolver.NXDOMAIN:
                results.append({
                    'selector': selector,
                    'source': source,
                    'priority': priority,
                    'found': False,
                    'record': None,
                    'record_preview': None,
                    'valid': False,
                    'error': 'DNS record not found',
                    'scan_time': datetime.utcnow()
                })
            except Exception as e:
                results.append({
                    'selector': selector,
                    'source': source,
                    'priority': priority,
                    'found': False,
                    'record': None,
                    'record_preview': None,
                    'valid': False,
                    'error': str(e),
                    'scan_time': datetime.utcnow()
                })
        
        return results
    
    def _store_discovered_selectors(self, domain: str, found_records: List[Dict[str, Any]]):
        """Store discovered selectors in the database"""
        for record in found_records:
            if record['source'] == 'brute_force':
                # Only store brute force discoveries
                dkim_selector_manager.add_discovered_selector(
                    domain=domain,
                    selector=record['selector'],
                    source='brute_force_scan',
                    verification_status='verified'
                )
    
    def _generate_recommendations(self, found_records: List[Dict[str, Any]], 
                                failed_selectors: List[Dict[str, Any]], 
                                selector_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on scan results"""
        recommendations = []
        
        if not found_records:
            recommendations.append({
                'type': 'warning',
                'title': 'No DKIM Records Found',
                'description': 'No DKIM records were found for this domain. Consider adding DKIM authentication.',
                'priority': 'high'
            })
        else:
            # Analyze found records
            admin_selectors = [r for r in found_records if r['source'] == 'admin']
            discovered_selectors = [r for r in found_records if r['source'] == 'discovered']
            brute_force_selectors = [r for r in found_records if r['source'] == 'brute_force']
            
            if discovered_selectors:
                recommendations.append({
                    'type': 'info',
                    'title': 'Discovered DKIM Selectors',
                    'description': f'Found {len(discovered_selectors)} DKIM selectors through discovery. Consider adding these as admin-managed selectors.',
                    'priority': 'medium'
                })
            
            if brute_force_selectors:
                recommendations.append({
                    'type': 'success',
                    'title': 'Brute Force Success',
                    'description': f'Successfully found {len(brute_force_selectors)} DKIM selectors through brute force scanning.',
                    'priority': 'low'
                })
            
            # Check for multiple selectors
            if len(found_records) > 1:
                recommendations.append({
                    'type': 'info',
                    'title': 'Multiple DKIM Selectors',
                    'description': f'Found {len(found_records)} DKIM selectors. This provides good authentication diversity.',
                    'priority': 'low'
                })
        
        # Performance recommendations
        if selector_data['sources']['brute_force'] > 5:
            recommendations.append({
                'type': 'info',
                'title': 'Optimize Selector List',
                'description': 'Consider reducing brute force selectors to improve scan performance.',
                'priority': 'medium'
            })
        
        return recommendations
    
    def _generate_description(self, found_records: List[Dict[str, Any]], 
                            selector_data: Dict[str, Any]) -> str:
        """Generate human-readable description of scan results"""
        if not found_records:
            return f"No DKIM records found (checked {selector_data['total_used']} selectors)"
        
        sources = []
        if selector_data['sources']['admin'] > 0:
            sources.append(f"{selector_data['sources']['admin']} admin-managed")
        if selector_data['sources']['discovered'] > 0:
            sources.append(f"{selector_data['sources']['discovered']} discovered")
        if selector_data['sources']['brute_force'] > 0:
            sources.append(f"{selector_data['sources']['brute_force']} brute force")
        
        source_text = ", ".join(sources)
        return f"Found {len(found_records)} DKIM record(s) from {source_text} selectors"
    
    def quick_scan(self, domain: str, custom_selector: Optional[str] = None) -> Dict[str, Any]:
        """
        Quick DKIM scan for performance-critical scenarios
        
        Only checks:
        1. Custom selector (if provided)
        2. High-priority admin selectors
        3. Most common selectors
        """
        # Get limited selector list for quick scan
        selector_data = dkim_selector_manager.get_domain_selectors(domain, custom_selector)
        
        # Limit to first 5 selectors for quick scan
        quick_selectors = selector_data['selectors'][:5]
        
        # Scan limited selectors
        scan_results = self._scan_selectors(domain, quick_selectors)
        
        found_records = [r for r in scan_results if r['found']]
        
        return {
            'domain': domain,
            'has_dkim': len(found_records) > 0,
            'records': found_records,
            'selectors_checked': len(quick_selectors),
            'quick_scan': True,
            'status': 'Valid' if found_records else 'Not Found',
            'description': f"Quick scan: {'Found' if found_records else 'No'} DKIM records (checked {len(quick_selectors)} selectors)"
        }

# Global instance
enhanced_dkim_scanner = EnhancedDKIMScanner()
