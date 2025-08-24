import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

def parse_dmarc_record(record_text: str) -> Dict[str, Any]:
    """
    Parse DMARC record and extract all components for granular scoring
    Returns a dictionary with parsed components and their values
    """
    components = {
        'version': None,
        'policy': None,
        'subdomain_policy': None,
        'percentage': None,
        'rua': None,
        'ruf': None,
        'fo': None,
        'adkim': None,
        'aspf': None,
        'rf': None,
        'ri': None,
        'sp': None,
        'valid': False,
        'warnings': []
    }
    
    try:
        # Basic validation
        if not record_text.startswith('v=DMARC1'):
            components['warnings'].append('Invalid DMARC version')
            return components
        
        components['version'] = 'DMARC1'
        components['valid'] = True
        
        # Parse all components
        parts = record_text.split(';')
        for part in parts:
            part = part.strip()
            if '=' not in part:
                continue
                
            key, value = part.split('=', 1)
            key = key.strip().lower()
            value = value.strip()
            
            if key == 'p':
                components['policy'] = value
            elif key == 'sp':
                components['subdomain_policy'] = value
            elif key == 'pct':
                try:
                    components['percentage'] = int(value)
                except ValueError:
                    components['warnings'].append(f'Invalid percentage value: {value}')
            elif key == 'rua':
                components['rua'] = value
            elif key == 'ruf':
                components['ruf'] = value
            elif key == 'fo':
                components['fo'] = value
            elif key == 'adkim':
                components['adkim'] = value
            elif key == 'aspf':
                components['aspf'] = value
            elif key == 'rf':
                components['rf'] = value
            elif key == 'ri':
                try:
                    components['ri'] = int(value)
                except ValueError:
                    components['warnings'].append(f'Invalid report interval: {value}')
        
        # Validation checks
        if not components['policy']:
            components['warnings'].append('Missing policy (p=)')
        if components['policy'] and components['policy'] not in ['none', 'quarantine', 'reject']:
            components['warnings'].append(f'Invalid policy value: {components["policy"]}')
        if components['percentage'] and (components['percentage'] < 0 or components['percentage'] > 100):
            components['warnings'].append(f'Invalid percentage: {components["percentage"]}')
            
    except Exception as e:
        components['warnings'].append(f'Parsing error: {str(e)}')
        components['valid'] = False
    
    return components

def parse_spf_record(record_text: str) -> Dict[str, Any]:
    """
    Parse SPF record and extract components for granular scoring
    """
    components = {
        'version': None,
        'policy': None,
        'mechanisms': [],
        'includes': [],
        'ips': [],
        'redirects': [],
        'valid': False,
        'warnings': []
    }
    
    try:
        if not record_text.startswith('v=spf1'):
            components['warnings'].append('Invalid SPF version')
            return components
        
        components['version'] = 'spf1'
        components['valid'] = True
        
        # Parse mechanisms
        mechanisms = record_text.split()
        for mech in mechanisms:
            if mech.startswith('v='):
                continue
            
            if mech.endswith('-all'):
                components['policy'] = 'reject'
            elif mech.endswith('~all'):
                components['policy'] = 'softfail'
            elif mech.endswith('?all'):
                components['policy'] = 'neutral'
            elif mech.endswith('+all'):
                components['policy'] = 'permissive'
            elif mech.startswith('include:'):
                components['includes'].append(mech[8:])
                components['mechanisms'].append('include')
            elif mech.startswith('ip4:') or mech.startswith('ip6:'):
                components['ips'].append(mech)
                components['mechanisms'].append('direct_ip')
            elif mech == 'a':
                components['mechanisms'].append('domain_a')
            elif mech == 'mx':
                components['mechanisms'].append('domain_mx')
            elif mech.startswith('redirect='):
                components['redirects'].append(mech[9:])
                components['mechanisms'].append('redirect')
        
        if not components['policy']:
            components['warnings'].append('No policy specified (missing -all, ~all, ?all, +all)')
            
    except Exception as e:
        components['warnings'].append(f'Parsing error: {str(e)}')
        components['valid'] = False
    
    return components

def parse_dkim_record(record_text: str) -> Dict[str, Any]:
    """
    Parse DKIM record and extract components for granular scoring
    """
    components = {
        'version': None,
        'algorithm': None,
        'key_type': None,
        'key_length': None,
        'valid': False,
        'warnings': []
    }
    
    try:
        if not record_text.startswith('v=DKIM1'):
            components['warnings'].append('Invalid DKIM version')
            return components
        
        components['version'] = 'DKIM1'
        components['valid'] = True
        
        # Parse key components
        parts = record_text.split(';')
        for part in parts:
            part = part.strip()
            if '=' not in part:
                continue
            
            key, value = part.split('=', 1)
            key = key.strip().lower()
            value = value.strip()
            
            if key == 'k':
                components['algorithm'] = value
            elif key == 'p':
                # Extract key length from public key
                if value.startswith('MII'):
                    # RSA key
                    components['key_type'] = 'RSA'
                    # Estimate key length (this is simplified)
                    key_length = len(value) * 6 // 8  # Base64 to bits approximation
                    if key_length >= 2048:
                        components['key_length'] = 2048
                    elif key_length >= 1024:
                        components['key_length'] = 1024
                    else:
                        components['key_length'] = 512
                elif value.startswith('MC'):
                    # Ed25519 key
                    components['key_type'] = 'Ed25519'
                    components['key_length'] = 256
        
        # Determine algorithm strength
        if components['key_type'] == 'Ed25519':
            components['algorithm'] = 'strong'
        elif components['key_type'] == 'RSA' and components['key_length'] >= 2048:
            components['algorithm'] = 'strong'
        else:
            components['algorithm'] = 'weak'
            
    except Exception as e:
        components['warnings'].append(f'Parsing error: {str(e)}')
        components['valid'] = False
    
    return components

def analyze_mx_records(mx_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze MX records for granular scoring
    """
    analysis = {
        'count': len(mx_records),
        'has_trusted_provider': False,
        'has_provider': len(mx_records) > 0,
        'secure_configuration': True,  # Default assumption
        'providers': []
    }
    
    if not mx_records:
        return analysis
    
    # Check for trusted providers
    trusted_providers = ['google', 'microsoft', 'outlook', 'office365', 'gmail']
    for record in mx_records:
        server = record.get('server', '').lower()
        analysis['providers'].append(server)
        
        for provider in trusted_providers:
            if provider in server:
                analysis['has_trusted_provider'] = True
                break
    
    # Check for secure configuration (basic checks)
    for record in mx_records:
        server = record.get('server', '')
        if not server or server == 'localhost':
            analysis['secure_configuration'] = False
    
    return analysis
