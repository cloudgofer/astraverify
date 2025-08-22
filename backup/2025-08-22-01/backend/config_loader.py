import json
import csv
import pandas as pd
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ConfigLoader:
    """Hybrid configuration loader for scoring system"""
    
    def __init__(self, config_dir: str = 'config'):
        self.config_dir = Path(config_dir)
        self.scoring_structure = None
        self.rule_weights = None
        self.recommendations = None
        self.grading = None
        self._load_all_configs()
    
    def _load_all_configs(self):
        """Load all configuration files"""
        try:
            # Load JSON structure
            with open(self.config_dir / 'scoring_structure.json', 'r') as f:
                self.scoring_structure = json.load(f)
            
            # Load CSV configurations
            self.rule_weights = pd.read_csv(self.config_dir / 'rule_weights.csv')
            self.recommendations = pd.read_csv(self.config_dir / 'recommendations.csv')
            self.grading = pd.read_csv(self.config_dir / 'grading.csv')
            
            logger.info(f"Loaded configuration version {self.scoring_structure.get('version', 'unknown')}")
            
        except FileNotFoundError as e:
            logger.error(f"Configuration file not found: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise
    
    def get_component_rules(self, component: str) -> List[Dict[str, Any]]:
        """Get rules for a specific component"""
        if component not in self.scoring_structure['components']:
            logger.warning(f"Unknown component: {component}")
            return []
        
        rules = self.rule_weights[self.rule_weights['component'] == component]
        return rules.to_dict('records')
    
    def get_rule_points(self, component: str, rule: str, condition: str) -> float:
        """Get points for a specific rule condition"""
        rule_data = self.rule_weights[
            (self.rule_weights['component'] == component) &
            (self.rule_weights['rule'] == rule) &
            (self.rule_weights['condition'] == condition)
        ]
        
        if rule_data.empty:
            logger.warning(f"No rule found for {component}.{rule}.{condition}")
            return 0.0
        
        return float(rule_data.iloc[0]['points'])
    
    def get_recommendations(self, component: str = None) -> List[Dict[str, Any]]:
        """Get recommendations, optionally filtered by component"""
        if component:
            recs = self.recommendations[self.recommendations['component'] == component]
        else:
            recs = self.recommendations
        return recs.to_dict('records')
    
    def get_grade(self, score: float) -> Dict[str, Any]:
        """Get grade information based on score"""
        for _, row in self.grading.iterrows():
            if score >= row['min_score']:
                return {
                    'grade': row['grade'],
                    'description': row['description'],
                    'color': row['color'],
                    'min_score': row['min_score']
                }
        return {
            'grade': 'F',
            'description': 'No email security',
            'color': '#F44336',
            'min_score': 0
        }
    
    def get_status(self, score: float) -> str:
        """Get status description based on score"""
        if score >= 90:
            return 'Excellent'
        elif score >= 75:
            return 'Good'
        elif score >= 50:
            return 'Fair'
        elif score >= 25:
            return 'Poor'
        else:
            return 'Very Poor'
    
    def validate_configuration(self) -> List[str]:
        """Validate configuration integrity"""
        errors = []
        
        # Check if all components in structure have rules
        for component in self.scoring_structure['components']:
            component_rules = self.rule_weights[self.rule_weights['component'] == component]
            if component_rules.empty:
                errors.append(f"No rules found for component: {component}")
        
        # Check for duplicate rules
        duplicates = self.rule_weights.duplicated(subset=['component', 'rule', 'condition'], keep=False)
        if duplicates.any():
            errors.append("Duplicate rules found in rule_weights.csv")
        
        return errors
    
    def export_configs_to_csv(self):
        """Export current JSON configs to CSV for editing"""
        # Export rule weights template
        rules_data = []
        for component, config in self.scoring_structure['components'].items():
            for rule in config['rules']:
                rules_data.append({
                    'component': component,
                    'rule': rule,
                    'condition': f'{rule}_condition',
                    'points': 0,
                    'description': f'{rule} rule for {component}'
                })
        
        pd.DataFrame(rules_data).to_csv(self.config_dir / 'rule_weights_template.csv', index=False)
        logger.info("Exported rule_weights_template.csv")
    
    def reload_configs(self):
        """Reload all configuration files"""
        logger.info("Reloading configuration files...")
        self._load_all_configs()
        logger.info("Configuration reloaded successfully")
