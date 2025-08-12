# Granular Scoring System Implementation

## Overview

This document describes the implementation of the hybrid granular scoring system for AstraVerify's email security analysis.

## Architecture

### Hybrid Configuration System

The system uses a hybrid approach combining:
- **JSON files**: Complex structure and validation schemas
- **CSV files**: Easily editable weights, recommendations, and grading thresholds

### File Structure

```
backend/
├── config/
│   ├── scoring_structure.json    # Component definitions and validation
│   ├── rule_weights.csv          # Scoring rules and points
│   ├── recommendations.csv       # Actionable recommendations
│   └── grading.csv              # Grade thresholds and colors
├── config_loader.py              # Hybrid configuration loader
├── parsers.py                    # DNS record parsers
├── scoring_engine.py             # Granular scoring engine
├── recommendation_engine.py      # Recommendation generator
└── app_new.py                    # Updated Flask application
```

## Configuration Files

### 1. scoring_structure.json
Defines the overall structure of the scoring system:
- Component definitions (MX, SPF, DMARC, DKIM)
- Maximum scores per component
- Validation rules
- Version information

### 2. rule_weights.csv
Contains all scoring rules with their conditions and point values:
```csv
component,rule,condition,points,description
mx,base,has_mx_records,15,"Basic MX record presence"
mx,redundancy,mx_count >= 3,5,"3 or more MX records for redundancy"
```

### 3. recommendations.csv
Contains actionable recommendations based on analysis results:
```csv
component,condition,type,priority,title,description,impact,effort,action,example,estimated_time,technical_details
```

### 4. grading.csv
Defines grade thresholds and colors:
```csv
grade,min_score,description,color
A+,95,Outstanding email security,#4CAF50
A,90,Excellent email security,#4CAF50
```

## Scoring Components

### MX Records (25 points max)
- **Base**: 15 points for presence
- **Redundancy**: 5 points for multiple records
- **Provider**: 3 points for trusted providers
- **Security**: 2 points for secure configuration

### SPF Records (25 points max)
- **Base**: 10 points for presence
- **Policy**: 8 points for policy strength (-all > ~all > ?all)
- **Mechanisms**: 5 points for mechanism quality
- **Security**: 2 points for security features

### DMARC Records (30 points max)
- **Base**: 15 points for presence
- **Policy**: 12 points for policy configuration
- **Coverage**: 3 points for percentage coverage
- **Reporting**: 3 points for reporting configuration

### DKIM Records (25 points max)
- **Base**: 15 points for presence
- **Selectors**: 5 points for selector diversity
- **Algorithm**: 3 points for algorithm strength
- **Key Length**: 2 points for key length

## Usage

### Basic Usage
```python
from backend.config_loader import ConfigLoader
from backend.scoring_engine import ScoringEngine
from backend.recommendation_engine import RecommendationEngine

# Initialize
config = ConfigLoader('backend/config')
scoring_engine = ScoringEngine(config)
recommendation_engine = RecommendationEngine(config)

# Calculate scores
component_scores = {
    'mx': scoring_engine.calculate_component_score('mx', mx_data),
    'spf': scoring_engine.calculate_component_score('spf', spf_data),
    'dmarc': scoring_engine.calculate_component_score('dmarc', dmarc_data),
    'dkim': scoring_engine.calculate_component_score('dkim', dkim_data)
}

# Get total score
total_score = scoring_engine.calculate_total_score(component_scores)

# Generate recommendations
recommendations = recommendation_engine.generate_recommendations(component_scores, parsed_data)
```

### Modifying Scoring Rules

To modify scoring rules, edit the CSV files:

1. **Change point values**: Edit `rule_weights.csv`
2. **Add new recommendations**: Edit `recommendations.csv`
3. **Adjust grade thresholds**: Edit `grading.csv`

### Adding New Components

1. Add component definition to `scoring_structure.json`
2. Add rules to `rule_weights.csv`
3. Add recommendations to `recommendations.csv`
4. Implement scoring logic in `scoring_engine.py`

## Benefits

### 1. Maintainability
- Scoring rules separated from code
- Easy to modify weights without code changes
- Version control friendly

### 2. Flexibility
- Different scoring models for different use cases
- Environment-specific configurations
- A/B testing capabilities

### 3. Transparency
- Clear documentation of scoring rules
- Easy to audit and validate
- Stakeholder review without code changes

### 4. Performance
- JSON for complex operations
- CSV for easy editing
- Efficient loading and caching

## Migration from Legacy System

The new system maintains backward compatibility:
- Legacy `get_security_score()` function still works
- Progressive loading still supported
- All existing API endpoints preserved

## Testing

```bash
# Test configuration loading
python3 -c "from backend.config_loader import ConfigLoader; print(ConfigLoader('backend/config').scoring_structure['version'])"

# Test scoring engine
python3 -c "from backend.config_loader import ConfigLoader; from backend.scoring_engine import ScoringEngine; config = ConfigLoader('backend/config'); engine = ScoringEngine(config); print('Success')"
```

## Deployment

1. **Development**: Use feature branch
2. **Staging**: Merge to staging branch
3. **Production**: Merge to production branch

## Future Enhancements

1. **Admin Interface**: Web interface for editing CSV files
2. **A/B Testing**: Multiple scoring configurations
3. **Analytics**: Track scoring rule effectiveness
4. **Machine Learning**: Dynamic scoring adjustments
