from flask import Flask, request, jsonify
from flask_cors import CORS
import dns.resolver
import logging
import re
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from firestore_config import firestore_manager

# Import new scoring system
from config_loader import ConfigLoader
from scoring_engine import ScoringEngine
from recommendation_engine import RecommendationEngine

# Configure DNS resolver for better reliability
dns.resolver.default_resolver = dns.resolver.Resolver(configure=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize scoring system
config_loader = ConfigLoader('config')
scoring_engine = ScoringEngine(config_loader)
recommendation_engine = RecommendationEngine(config_loader)

# Environment configuration
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'production')
logger.info(f"Starting AstraVerify backend in {ENVIRONMENT} environment")

# Admin authentication
ADMIN_API_KEY = os.environ.get('ADMIN_API_KEY', 'astraverify-admin-2024')

# Email configuration
EMAIL_SENDER = 'hi@astraverify.com'
EMAIL_SMTP_SERVER = 'smtp.dreamhost.com'  # DreamHost SMTP server
EMAIL_SMTP_PORT = 587
EMAIL_USERNAME = 'hi@astraverify.com'

# Get email password from environment or GCP Secret Manager
def get_email_password():
    """Get email password from environment or GCP Secret Manager"""
    # First try environment variable
    password = os.environ.get('EMAIL_PASSWORD')
    if password:
        logger.info("Using EMAIL_PASSWORD from environment variable")
        return password
    
    # If not in environment, try GCP Secret Manager
    try:
        from google.cloud import secretmanager
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/astraverify/secrets/astraverify-email-password/versions/latest"
        response = client.access_secret_version(request={"name": name})
        logger.info("Using EMAIL_PASSWORD from GCP Secret Manager")
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.warning(f"Failed to get password from Secret Manager: {e}")
        return None

EMAIL_PASSWORD = get_email_password()

def require_admin_auth(f):
    """Decorator to require admin authentication"""
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-Admin-API-Key')
        if api_key != ADMIN_API_KEY:
            return jsonify({"error": "Admin access required"}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def get_mx_details(domain):
    """Get detailed MX record information"""
    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        records = []
        for mx in mx_records:
            records.append({
                'priority': mx.preference,
                'server': str(mx.exchange),
                'valid': True
            })
        
        # Sort MX records by priority (lower priority number = higher priority)
        records.sort(key=lambda x: x['priority'])
        
        return {
            'has_mx': True,
            'records': records,
            'status': 'Valid',
            'description': f'Found {len(records)} MX record(s)'
        }
    except Exception as e:
        logger.warning(f"MX check failed for {domain}: {str(e)}")
        return {
            'has_mx': False,
            'records': [],
            'status': 'Missing',
            'description': 'No MX records found'
        }

def get_spf_details(domain):
    """Get detailed SPF record information"""
    try:
        txt_records = dns.resolver.resolve(domain, 'TXT')
        spf_records = []
        for record in txt_records:
            record_text = record.to_text().strip('"')
            if record_text.startswith('v=spf1'):
                spf_records.append({
                    'record': record_text,
                    'valid': True
                })
        
        if spf_records:
            return {
                'has_spf': True,
                'records': spf_records,
                'status': 'Valid',
                'description': f'Found {len(spf_records)} SPF record(s)'
            }
        else:
            return {
                'has_spf': False,
                'records': [],
                'status': 'Missing',
                'description': 'No SPF records found'
            }
    except Exception as e:
        logger.warning(f"SPF check failed for {domain}: {str(e)}")
        return {
            'has_spf': False,
            'records': [],
            'status': 'Missing',
            'description': 'No SPF records found'
        }

def get_dmarc_details(domain):
    """Get detailed DMARC record information"""
    try:
        logger.info(f"Attempting to resolve DMARC for {domain}")
        dmarc_records = dns.resolver.resolve(f"_dmarc.{domain}", 'TXT')
        logger.info(f"Successfully resolved DMARC for {domain}: {len(dmarc_records)} records")
        records = []
        for record in dmarc_records:
            record_text = record.to_text().strip('"')
            if record_text.startswith('v=DMARC1'):
                records.append({
                    'record': record_text,
                    'valid': True
                })
        
        if records:
            logger.info(f"DMARC validation successful for {domain}")
            return {
                'has_dmarc': True,
                'records': records,
                'status': 'Valid',
                'description': f'Found {len(records)} DMARC record(s)'
            }
        else:
            logger.warning(f"DMARC records found but none are valid for {domain}")
            return {
                'has_dmarc': False,
                'records': [],
                'status': 'Missing',
                'description': 'No DMARC records found'
            }
    except Exception as e:
        logger.warning(f"DMARC check failed for {domain}: {str(e)}")
        return {
            'has_dmarc': False,
            'records': [],
            'status': 'Missing',
            'description': 'No DMARC records found'
        }

def get_dkim_details(domain, custom_selector=None):
    """Get DKIM record information (comprehensive check)"""
    # Load comprehensive DKIM selectors from file
    try:
        with open('resources/dkim_selectors.txt', 'r') as f:
            common_selectors = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        # Fallback to common selectors if file not found
        common_selectors = ['default', 'google', 'k1', 'selector1', 'selector2', 'dreamhost', 'mailgun', 'sendgrid', 'zoho', 'yahoo']
    
    # Add custom selector if provided
    if custom_selector and custom_selector not in common_selectors:
        common_selectors.insert(0, custom_selector)  # Add at beginning for priority
    
    dkim_records = []
    
    for selector in common_selectors:
        try:
            dkim_domain = f"{selector}._domainkey.{domain}"
            records = dns.resolver.resolve(dkim_domain, 'TXT')
            for record in records:
                record_text = record.to_text().strip('"')
                if record_text.startswith('v=DKIM1'):
                    dkim_records.append({
                        'selector': selector,
                        'record': record_text[:100] + '...' if len(record_text) > 100 else record_text,
                        'valid': True,
                        'full_record': record_text
                    })
        except:
            continue
    
    if dkim_records:
        return {
            'has_dkim': True,
            'records': dkim_records,
            'status': 'Valid',
            'description': f'Found {len(dkim_records)} DKIM record(s)',
            'selectors_checked': len(common_selectors)
        }
    else:
        return {
            'has_dkim': False,
            'records': [],
            'status': 'Not Found',
            'description': f'No DKIM records found (checked {len(common_selectors)} selectors)',
            'selectors_checked': len(common_selectors)
        }

def detect_email_provider(mx_result, spf_result, dkim_result):
    """Detect the email service provider based on MX, SPF, and DKIM records"""
    provider = "Unknown"
    
    # Check for Google Workspace
    google_indicators = [
        any('google' in r['server'].lower() for r in mx_result['records']),
        any('_spf.google.com' in r['record'] for r in spf_result['records']),
        any(r['selector'] == 'google' for r in dkim_result['records'])
    ]
    
    if any(google_indicators):
        provider = "Google Workspace"
    
    # Check for Microsoft 365
    microsoft_indicators = [
        any('outlook' in r['server'].lower() or 'microsoft' in r['server'].lower() for r in mx_result['records']),
        any('_spf.protection.outlook.com' in r['record'] for r in spf_result['records']),
        any(r['selector'] in ['selector1', 'selector2'] for r in dkim_result['records'])
    ]
    
    if any(microsoft_indicators):
        provider = "Microsoft 365"
    
    # Check for other common providers
    if any('yahoo' in r['server'].lower() for r in mx_result['records']):
        provider = "Yahoo"
    elif any('zoho' in r['server'].lower() for r in mx_result['records']):
        provider = "Zoho"
    elif any('mailgun' in r['server'].lower() for r in mx_result['records']):
        provider = "Mailgun"
    elif any('sendgrid' in r['server'].lower() for r in mx_result['records']):
        provider = "SendGrid"
    elif any(r['selector'] == 'dreamhost' for r in dkim_result['records']):
        provider = "DreamHost"
    
    return provider

def get_security_score_granular(mx_result, spf_result, dmarc_result, dkim_result):
    """Calculate comprehensive security score using new granular scoring system"""
    
    # Calculate component scores
    component_scores = {}
    for component_name in ['mx', 'spf', 'dmarc', 'dkim']:
        if component_name == 'mx':
            component_data = mx_result
        elif component_name == 'spf':
            component_data = spf_result
        elif component_name == 'dmarc':
            component_data = dmarc_result
        elif component_name == 'dkim':
            component_data = dkim_result
        
        component_scores[component_name] = scoring_engine.calculate_component_score(component_name, component_data)
    
    # Calculate total score
    total_score = scoring_engine.calculate_total_score(component_scores)
    
    return total_score

def generate_recommendations_granular(component_scores, mx_result, spf_result, dmarc_result, dkim_result):
    """Generate recommendations using new granular system"""
    
    parsed_data = {
        'mx': mx_result,
        'spf': spf_result,
        'dmarc': dmarc_result,
        'dkim': dkim_result
    }
    
    return recommendation_engine.generate_recommendations(component_scores, parsed_data)

# Legacy function for backward compatibility
def get_security_score(mx_result, spf_result, dmarc_result, dkim_result):
    """Legacy scoring function - now uses granular system"""
    return get_security_score_granular(mx_result, spf_result, dmarc_result, dkim_result)

@app.route('/api/check', methods=['GET'])
def check_domain():
    """Main domain checking endpoint with granular scoring"""
    domain = request.args.get('domain')
    progressive = request.args.get('progressive', 'false').lower() == 'true'
    
    if not domain:
        return jsonify({"error": "Domain parameter is required"}), 400
    
    # Remove protocol if present
    domain = domain.replace('http://', '').replace('https://', '').replace('www.', '')
    
    logger.info(f"Starting comprehensive analysis for domain: {domain}")
    
    # Get detailed results for each check
    mx_result = get_mx_details(domain)
    spf_result = get_spf_details(domain)
    dmarc_result = get_dmarc_details(domain)
    
    if progressive:
        # Progressive mode - return early results without DKIM
        logger.info(f"Progressive mode: returning early results for {domain}")
        
        # Calculate scores for available components
        component_scores = {
            'mx': scoring_engine.calculate_component_score('mx', mx_result),
            'spf': scoring_engine.calculate_component_score('spf', spf_result),
            'dmarc': scoring_engine.calculate_component_score('dmarc', dmarc_result),
            'dkim': {'score': 0, 'bonus': 0, 'total': 0, 'details': {}}
        }
        
        # Calculate total score
        total_score = scoring_engine.calculate_total_score(component_scores)
        
        # Generate recommendations
        recommendations = generate_recommendations_granular(component_scores, mx_result, spf_result, dmarc_result, {'has_dkim': False, 'records': []})
        
        early_results = {
            "domain": domain,
            "analysis_timestamp": None,
            "security_score": total_score,
            "email_provider": "Unknown",  # Will be updated after DKIM check
            "mx": {
                "enabled": mx_result['has_mx'],
                "status": mx_result['status'],
                "description": mx_result['description'],
                "records": mx_result['records']
            },
            "spf": {
                "enabled": spf_result['has_spf'],
                "status": spf_result['status'],
                "description": spf_result['description'],
                "records": spf_result['records']
            },
            "dmarc": {
                "enabled": dmarc_result['has_dmarc'],
                "status": dmarc_result['status'],
                "description": dmarc_result['description'],
                "records": dmarc_result['records']
            },
            "dkim": {
                "enabled": False,
                "status": "Checking...",
                "description": "Comprehensive DKIM check in progress...",
                "records": [],
                "checking": True
            },
            "progressive": True,
            "message": "Initial results ready, DKIM check in progress...",
            "recommendations": recommendations
        }
        return jsonify(early_results)
    
    # Full analysis including DKIM
    dkim_result = get_dkim_details(domain)
    
    # Detect email provider
    email_provider = detect_email_provider(mx_result, spf_result, dkim_result)
    
    # Calculate granular scores
    component_scores = {
        'mx': scoring_engine.calculate_component_score('mx', mx_result),
        'spf': scoring_engine.calculate_component_score('spf', spf_result),
        'dmarc': scoring_engine.calculate_component_score('dmarc', dmarc_result),
        'dkim': scoring_engine.calculate_component_score('dkim', dkim_result)
    }
    
    # Calculate total score
    security_score = scoring_engine.calculate_total_score(component_scores)
    
    # Generate recommendations
    recommendations = generate_recommendations_granular(component_scores, mx_result, spf_result, dmarc_result, dkim_result)
    
    # Compile comprehensive results
    results = {
        "domain": domain,
        "analysis_timestamp": None,  # Will be set by frontend
        "security_score": security_score,
        "component_scores": component_scores,
        "mx": {
            "enabled": mx_result['has_mx'],
            "status": mx_result['status'],
            "description": mx_result['description'],
            "records": mx_result['records']
        },
        "spf": {
            "enabled": spf_result['has_spf'],
            "status": spf_result['status'],
            "description": spf_result['description'],
            "records": spf_result['records']
        },
        "dkim": {
            "enabled": dkim_result['has_dkim'],
            "status": dkim_result['status'],
            "description": dkim_result['description'],
            "records": dkim_result['records']
        },
        "dmarc": {
            "enabled": dmarc_result['has_dmarc'],
            "status": dmarc_result['status'],
            "description": dmarc_result['description'],
            "records": dmarc_result['records']
        },
        "email_provider": email_provider,
        "recommendations": recommendations,
        "progressive": False
    }
    
    return jsonify(results)

# Keep existing routes for backward compatibility
@app.route('/api/check/dkim', methods=['GET'])
def complete_dkim_check():
    """Complete DKIM check for progressive mode"""
    domain = request.args.get('domain')
    custom_selector = request.args.get('dkim_selector')
    
    if not domain:
        return jsonify({"error": "Domain parameter is required"}), 400
    
    # Remove protocol if present
    domain = domain.replace('http://', '').replace('https://', '').replace('www.', '')
    
    logger.info(f"Completing DKIM analysis for domain: {domain}")
    
    # Get DKIM results
    dkim_result = get_dkim_details(domain, custom_selector)
    
    # Detect email provider based on DKIM
    mx_result = get_mx_details(domain)
    spf_result = get_spf_details(domain)
    email_provider = detect_email_provider(mx_result, spf_result, dkim_result)
    
    # Calculate security score
    dmarc_result = get_dmarc_details(domain)
    component_scores = {
        'mx': scoring_engine.calculate_component_score('mx', mx_result),
        'spf': scoring_engine.calculate_component_score('spf', spf_result),
        'dmarc': scoring_engine.calculate_component_score('dmarc', dmarc_result),
        'dkim': scoring_engine.calculate_component_score('dkim', dkim_result)
    }
    security_score = scoring_engine.calculate_total_score(component_scores)
    
    return jsonify({
        "domain": domain,
        "dkim": {
            "enabled": dkim_result['has_dkim'],
            "status": dkim_result['status'],
            "description": dkim_result['description'],
            "records": dkim_result['records'],
            "selectors_checked": dkim_result.get('selectors_checked', 0)
        },
        "email_provider": email_provider,
        "security_score": security_score,
        "completed": True
    })

# Keep all other existing routes...
# (Copy the rest of the existing routes from the original app.py)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
