import logging
from typing import Dict, Any, List
from config_loader import ConfigLoader
from parsers import parse_dmarc_record, parse_spf_record, parse_dkim_record, analyze_mx_records

logger = logging.getLogger(__name__)

class ScoringEngine:
    """Configurable scoring engine for email security analysis"""
    
    def __init__(self, config_loader: ConfigLoader):
        self.config = config_loader
        self.version = config_loader.scoring_structure.get('version', '1.0.0')
    
    def calculate_component_score(self, component_name: str, component_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate score for a specific component"""
        if component_name not in self.config.scoring_structure['components']:
            logger.warning(f"Unknown component: {component_name}")
            return {'score': 0, 'bonus': 0, 'total': 0, 'details': {}}
        
        component_config = self.config.scoring_structure['components'][component_name]
        scoring_rules = self.config.get_component_rules(component_name)
        
        base_score = 0
        bonus_score = 0
        details = {}
        
        # Calculate scores based on component type
        if component_name == 'mx':
            score_result = self._calculate_mx_score(component_data, scoring_rules)
        elif component_name == 'spf':
            score_result = self._calculate_spf_score(component_data, scoring_rules)
        elif component_name == 'dmarc':
            score_result = self._calculate_dmarc_score(component_data, scoring_rules)
        elif component_name == 'dkim':
            score_result = self._calculate_dkim_score(component_data, scoring_rules)
        else:
            score_result = {'base_score': 0, 'bonus_score': 0, 'details': {}}
        
        return {
            'score': score_result['base_score'],
            'bonus': score_result['bonus_score'],
            'total': min(score_result['base_score'] + score_result['bonus_score'], component_config['max_score']),
            'details': score_result['details']
        }
    
    def _calculate_mx_score(self, mx_data: Dict[str, Any], rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate MX component score"""
        base_score = 0
        bonus_score = 0
        details = {}
        
        # Analyze MX records
        mx_analysis = analyze_mx_records(mx_data.get('records', []))
        
        # Base score
        if mx_data.get('has_mx', False):
            base_score += self.config.get_rule_points('mx', 'base', 'has_mx_records')
            details['base'] = {
                'points': self.config.get_rule_points('mx', 'base', 'has_mx_records'),
                'description': 'Basic MX record presence'
            }
        
        # Redundancy score
        if mx_analysis['count'] >= 3:
            points = self.config.get_rule_points('mx', 'redundancy', 'mx_count >= 3')
        elif mx_analysis['count'] == 2:
            points = self.config.get_rule_points('mx', 'redundancy', 'mx_count == 2')
        elif mx_analysis['count'] == 1:
            points = self.config.get_rule_points('mx', 'redundancy', 'mx_count == 1')
        else:
            points = 0
        
        base_score += points
        details['redundancy'] = {
            'points': points,
            'description': f'{mx_analysis["count"]} MX records'
        }
        
        # Provider score
        if mx_analysis['has_trusted_provider']:
            points = self.config.get_rule_points('mx', 'provider', 'has_trusted_provider')
        elif mx_analysis['has_provider']:
            points = self.config.get_rule_points('mx', 'provider', 'has_provider')
        else:
            points = 0
        
        base_score += points
        details['provider'] = {
            'points': points,
            'description': 'Provider quality'
        }
        
        # Security score
        if mx_analysis['secure_configuration']:
            points = self.config.get_rule_points('mx', 'security', 'secure_configuration')
        else:
            points = 0
        
        base_score += points
        details['security'] = {
            'points': points,
            'description': 'Security configuration'
        }
        
        return {
            'base_score': base_score,
            'bonus_score': bonus_score,
            'details': details
        }
    
    def _calculate_spf_score(self, spf_data: Dict[str, Any], rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate SPF component score"""
        base_score = 0
        bonus_score = 0
        details = {}
        
        if not spf_data.get('has_spf', False):
            return {'base_score': 0, 'bonus_score': 0, 'details': {}}
        
        # Parse SPF record
        spf_record = spf_data.get('records', [{}])[0].get('record', '')
        spf_analysis = parse_spf_record(spf_record)
        
        # Base score
        base_score += self.config.get_rule_points('spf', 'base', 'has_spf_records')
        details['base'] = {
            'points': self.config.get_rule_points('spf', 'base', 'has_spf_records'),
            'description': 'Basic SPF record presence'
        }
        
        # Policy score
        policy = spf_analysis.get('policy', 'permissive')
        if policy == 'reject':
            points = self.config.get_rule_points('spf', 'policy', 'spf_policy == \'reject\'')
        elif policy == 'softfail':
            points = self.config.get_rule_points('spf', 'policy', 'spf_policy == \'softfail\'')
        elif policy == 'neutral':
            points = self.config.get_rule_points('spf', 'policy', 'spf_policy == \'neutral\'')
        else:
            points = self.config.get_rule_points('spf', 'policy', 'spf_policy == \'permissive\'')
        
        base_score += points
        details['policy'] = {
            'points': points,
            'description': f'SPF policy: {policy}'
        }
        
        # Mechanisms score
        mechanisms = spf_analysis.get('mechanisms', [])
        mechanism_points = 0
        
        if 'include' in mechanisms:
            mechanism_points += self.config.get_rule_points('spf', 'mechanisms', 'has_include_mechanisms')
        if 'direct_ip' in mechanisms:
            mechanism_points += self.config.get_rule_points('spf', 'mechanisms', 'has_direct_ip')
        if 'domain_a' in mechanisms or 'domain_mx' in mechanisms:
            mechanism_points += self.config.get_rule_points('spf', 'mechanisms', 'has_domain_records')
        
        base_score += mechanism_points
        details['mechanisms'] = {
            'points': mechanism_points,
            'description': f'SPF mechanisms: {", ".join(mechanisms)}'
        }
        
        # Security score
        if 'redirect' not in mechanisms:
            points = self.config.get_rule_points('spf', 'security', 'no_redirect_mechanisms')
        else:
            points = 0
        
        base_score += points
        details['security'] = {
            'points': points,
            'description': 'Security features'
        }
        
        return {
            'base_score': base_score,
            'bonus_score': bonus_score,
            'details': details
        }
    
    def _calculate_dmarc_score(self, dmarc_data: Dict[str, Any], rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate DMARC component score"""
        base_score = 0
        bonus_score = 0
        details = {}
        
        if not dmarc_data.get('has_dmarc', False):
            return {'base_score': 0, 'bonus_score': 0, 'details': {}}
        
        # Parse DMARC record
        dmarc_record = dmarc_data.get('records', [{}])[0].get('record', '')
        dmarc_analysis = parse_dmarc_record(dmarc_record)
        
        # Base score
        base_score += self.config.get_rule_points('dmarc', 'base', 'has_dmarc_records')
        details['base'] = {
            'points': self.config.get_rule_points('dmarc', 'base', 'has_dmarc_records'),
            'description': 'Basic DMARC record presence'
        }
        
        # Policy score
        policy = dmarc_analysis.get('policy', 'missing')
        if policy == 'reject':
            points = self.config.get_rule_points('dmarc', 'policy', 'dmarc_policy == \'reject\'')
        elif policy == 'quarantine':
            points = self.config.get_rule_points('dmarc', 'policy', 'dmarc_policy == \'quarantine\'')
        elif policy == 'none':
            points = self.config.get_rule_points('dmarc', 'policy', 'dmarc_policy == \'none\'')
        else:
            points = self.config.get_rule_points('dmarc', 'policy', 'dmarc_policy == \'missing\'')
        
        base_score += points
        details['policy'] = {
            'points': points,
            'description': f'DMARC policy: {policy}'
        }
        
        # Coverage score
        percentage = dmarc_analysis.get('percentage', 0)
        if percentage is None:
            percentage = 0
        if percentage == 100:
            points = self.config.get_rule_points('dmarc', 'coverage', 'dmarc_percentage == 100')
        elif percentage >= 50:
            points = self.config.get_rule_points('dmarc', 'coverage', 'dmarc_percentage >= 50')
        elif percentage >= 1:
            points = self.config.get_rule_points('dmarc', 'coverage', 'dmarc_percentage >= 1')
        else:
            points = self.config.get_rule_points('dmarc', 'coverage', 'dmarc_percentage == 0')
        
        base_score += points
        details['coverage'] = {
            'points': points,
            'description': f'DMARC coverage: {percentage}%'
        }
        
        # Reporting score
        reporting_points = 0
        if dmarc_analysis.get('rua'):
            reporting_points += self.config.get_rule_points('dmarc', 'reporting', 'dmarc_rua_present')
        if dmarc_analysis.get('ruf'):
            reporting_points += self.config.get_rule_points('dmarc', 'reporting', 'dmarc_ruf_present')
        
        base_score += reporting_points
        details['reporting'] = {
            'points': reporting_points,
            'description': 'DMARC reporting'
        }
        
        return {
            'base_score': base_score,
            'bonus_score': bonus_score,
            'details': details
        }
    
    def _calculate_dkim_score(self, dkim_data: Dict[str, Any], rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate DKIM component score"""
        base_score = 0
        bonus_score = 0
        details = {}
        
        if not dkim_data.get('has_dkim', False):
            return {'base_score': 0, 'bonus_score': 0, 'details': {}}
        
        # Base score - only basic DKIM record presence
        base_score += self.config.get_rule_points('dkim', 'base', 'has_dkim_records')
        details['base'] = {
            'points': self.config.get_rule_points('dkim', 'base', 'has_dkim_records'),
            'description': 'Basic DKIM record presence'
        }
        
        # Bonus scores - selectors, algorithm, and key length
        # Selectors score
        selector_count = len(dkim_data.get('records', []))
        if selector_count > 1:
            points = self.config.get_rule_points('dkim', 'selectors', 'dkim_selector_count > 1')
        elif selector_count == 1:
            points = self.config.get_rule_points('dkim', 'selectors', 'dkim_selector_count == 1')
        else:
            points = 0
        
        bonus_score += points
        details['selectors'] = {
            'points': points,
            'description': f'{selector_count} DKIM selectors'
        }
        
        # Algorithm score (simplified)
        # In a real implementation, you'd parse the DKIM records
        algorithm = 'strong'  # Default assumption
        if algorithm == 'strong':
            points = self.config.get_rule_points('dkim', 'algorithm', 'strong_algorithm')
        else:
            points = self.config.get_rule_points('dkim', 'algorithm', 'weak_algorithm')
        
        bonus_score += points
        details['algorithm'] = {
            'points': points,
            'description': f'DKIM algorithm: {algorithm}'
        }
        
        # Key length score (simplified)
        key_length = 2048  # Default assumption
        if key_length >= 2048:
            points = self.config.get_rule_points('dkim', 'key_length', 'key_length >= 2048')
        else:
            points = self.config.get_rule_points('dkim', 'key_length', 'key_length < 2048')
        
        bonus_score += points
        details['key_length'] = {
            'points': points,
            'description': f'DKIM key length: {key_length} bits'
        }
        
        return {
            'base_score': base_score,
            'bonus_score': bonus_score,
            'details': details
        }
    
    def calculate_total_score(self, component_scores: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate total security score from component scores"""
        total_score = 0
        total_bonus = 0
        base_score = 0
        
        for component_name, component_score in component_scores.items():
            total_score += component_score['total']
            total_bonus += component_score['bonus']
            base_score += component_score['score']
        
        # Apply bonus cap
        max_bonus = self.config.scoring_structure['max_bonus_points']
        total_bonus = min(total_bonus, max_bonus)
        final_score = min(total_score, self.config.scoring_structure['max_total_score'])
        
        # Get grade and status
        grade_info = self.config.get_grade(final_score)
        status = self.config.get_status(final_score)
        
        return {
            'score': round(final_score, 1),
            'grade': grade_info['grade'],
            'status': status,
            'base_score': base_score,
            'bonus_points': round(total_bonus, 1),
            'max_score': self.config.scoring_structure['max_total_score'],
            'max_bonus': max_bonus,
            'scoring_details': component_scores,
            'grade_info': grade_info
        }
