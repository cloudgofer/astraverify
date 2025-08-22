import logging
from typing import Dict, Any, List
from config_loader import ConfigLoader

logger = logging.getLogger(__name__)

class RecommendationEngine:
    """Generate specific, actionable recommendations based on granular analysis"""
    
    def __init__(self, config_loader: ConfigLoader):
        self.config = config_loader
        self.recommendations = []
    
    def generate_recommendations(self, component_scores: Dict[str, Dict[str, Any]], 
                                parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate comprehensive recommendations based on granular analysis"""
        recommendations = []
        
        # Component-specific recommendations
        mx_recs = self._generate_mx_recommendations(component_scores.get('mx', {}), parsed_data.get('mx', {}))
        recommendations.extend(mx_recs)
        
        spf_recs = self._generate_spf_recommendations(component_scores.get('spf', {}), parsed_data.get('spf', {}))
        recommendations.extend(spf_recs)
        
        dmarc_recs = self._generate_dmarc_recommendations(component_scores.get('dmarc', {}), parsed_data.get('dmarc', {}))
        recommendations.extend(dmarc_recs)
        
        dkim_recs = self._generate_dkim_recommendations(component_scores.get('dkim', {}), parsed_data.get('dkim', {}))
        recommendations.extend(dkim_recs)
        
        # Cross-component recommendations
        cross_recs = self._generate_cross_component_recommendations(component_scores, parsed_data)
        recommendations.extend(cross_recs)
        
        return self._prioritize_recommendations(recommendations)
    
    def _generate_mx_recommendations(self, mx_score: Dict[str, Any], mx_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate MX-specific recommendations"""
        recommendations = []
        
        # Check if MX records are completely missing
        if not mx_data.get('has_mx', False):
            rec = self._get_recommendation('mx', 'mx_records_missing')
            if rec:
                recommendations.append(rec)
            return recommendations  # Return early if no MX records
        
        # Check base score (presence of MX records)
        base_score = mx_score.get('details', {}).get('base', {}).get('points', 0)
        if base_score == 0:
            rec = self._get_recommendation('mx', 'mx_base_score == 0')
            if rec:
                recommendations.append(rec)
        
        # Check redundancy
        redundancy_score = mx_score.get('details', {}).get('redundancy', {}).get('points', 0)
        if redundancy_score < 3:
            rec = self._get_recommendation('mx', 'mx_redundancy_score < 3')
            if rec:
                recommendations.append(rec)
        
        # Check provider quality
        provider_score = mx_score.get('details', {}).get('provider', {}).get('points', 0)
        if provider_score < 3:
            rec = self._get_recommendation('mx', 'mx_provider_score < 3')
            if rec:
                recommendations.append(rec)
        
        return recommendations
    
    def _generate_spf_recommendations(self, spf_score: Dict[str, Any], spf_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate SPF-specific recommendations"""
        recommendations = []
        
        # Check policy strength
        policy_score = spf_score.get('details', {}).get('policy', {}).get('points', 0)
        if policy_score < 5:
            rec = self._get_recommendation('spf', 'spf_policy_score < 5')
            if rec:
                recommendations.append(rec)
        
        # Check mechanisms
        mechanism_score = spf_score.get('details', {}).get('mechanisms', {}).get('points', 0)
        if mechanism_score < 3:
            rec = self._get_recommendation('spf', 'spf_mechanism_score < 3')
            if rec:
                recommendations.append(rec)
        
        return recommendations
    
    def _generate_dmarc_recommendations(self, dmarc_score: Dict[str, Any], dmarc_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate DMARC-specific recommendations"""
        recommendations = []
        
        # Get parsed DMARC data
        dmarc_records = dmarc_data.get('records', [])
        if dmarc_records:
            from parsers import parse_dmarc_record
            parsed_dmarc = parse_dmarc_record(dmarc_records[0].get('record', ''))
            
            # Check policy
            if parsed_dmarc.get('policy') == 'none':
                rec = self._get_recommendation('dmarc', 'dmarc_policy == \'none\'')
                if rec:
                    recommendations.append(rec)
            elif parsed_dmarc.get('policy') == 'quarantine':
                rec = self._get_recommendation('dmarc', 'dmarc_policy == \'quarantine\'')
                if rec:
                    recommendations.append(rec)
            
            # Check coverage
            if parsed_dmarc.get('percentage') != 100:
                rec = self._get_recommendation('dmarc', 'dmarc_percentage != 100')
                if rec:
                    recommendations.append(rec)
            
            # Check reporting
            if not parsed_dmarc.get('rua'):
                rec = self._get_recommendation('dmarc', 'dmarc_rua_missing')
                if rec:
                    recommendations.append(rec)
        
        return recommendations
    
    def _generate_dkim_recommendations(self, dkim_score: Dict[str, Any], dkim_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate DKIM-specific recommendations"""
        recommendations = []
        
        # Check selectors
        selector_score = dkim_score.get('details', {}).get('selectors', {}).get('points', 0)
        if selector_score < 3:
            rec = self._get_recommendation('dkim', 'dkim_selector_score < 3')
            if rec:
                recommendations.append(rec)
        
        # Check algorithm
        algorithm_score = dkim_score.get('details', {}).get('algorithm', {}).get('points', 0)
        if algorithm_score < 3:
            rec = self._get_recommendation('dkim', 'dkim_algorithm_score < 3')
            if rec:
                recommendations.append(rec)
        
        return recommendations
    
    def _generate_cross_component_recommendations(self, component_scores: Dict[str, Dict[str, Any]], 
                                                parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations that span multiple components"""
        recommendations = []
        
        # Check for missing critical components
        missing_components = []
        if component_scores.get('spf', {}).get('total', 0) == 0:
            missing_components.append('SPF')
        if component_scores.get('dkim', {}).get('total', 0) == 0:
            missing_components.append('DKIM')
        if component_scores.get('dmarc', {}).get('total', 0) == 0:
            missing_components.append('DMARC')
        
        if len(missing_components) >= 2:
            rec = self._get_recommendation('cross_component', 'missing_critical_components >= 2')
            if rec:
                rec['description'] = rec['description'].replace('critical email security components', 
                                                               f'{", ".join(missing_components)} records')
                recommendations.append(rec)
        
        # Check for weak overall configuration
        total_score = sum(comp.get('total', 0) for comp in component_scores.values())
        if total_score < 60:
            rec = self._get_recommendation('cross_component', 'total_score < 60')
            if rec:
                recommendations.append(rec)
        
        return recommendations
    
    def _get_recommendation(self, component: str, condition: str) -> Dict[str, Any]:
        """Get recommendation from configuration"""
        recs = self.config.recommendations[
            (self.config.recommendations['component'] == component) &
            (self.config.recommendations['condition'] == condition)
        ]
        
        if recs.empty:
            logger.warning(f"No recommendation found for {component}.{condition}")
            return None
        
        rec = recs.iloc[0]
        return {
            'component': rec['component'],
            'type': rec['type'],
            'priority': rec['priority'],
            'title': rec['title'],
            'description': rec['description'],
            'impact': rec['impact'],
            'effort': rec['effort'],
            'action': rec['action'],
            'example': rec['example'],
            'estimated_time': rec['estimated_time'],
            'technical_details': rec['technical_details']
        }
    
    def _prioritize_recommendations(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort recommendations by priority and type"""
        priority_order = {
            'critical': 1,
            'important': 2,
            'info': 3
        }
        
        return sorted(recommendations, key=lambda x: (
            priority_order.get(x['type'], 4),
            x['priority'] == 'high',
            x['component'] != 'cross_component'
        ))
