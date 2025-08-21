from datetime import datetime
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

# Import enhanced DKIM components
from dkim_selector_manager import dkim_selector_manager
from enhanced_dkim_scanner import enhanced_dkim_scanner
from admin_api import create_admin_routes
from admin_ui import create_admin_ui_routes

# Configure DNS resolver for better reliability
dns.resolver.default_resolver = dns.resolver.Resolver(configure=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Environment configuration
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'local')
logger.info(f"Starting AstraVerify backend with ENHANCED DKIM in {ENVIRONMENT} environment")

# Admin authentication
ADMIN_API_KEY = os.environ.get('ADMIN_API_KEY', 'astraverify-admin-2024')

# Email configuration
EMAIL_SENDER = 'hi@astraverify.com'
EMAIL_SMTP_SERVER = 'smtp.gmail.com'
EMAIL_SMTP_PORT = 587
EMAIL_USERNAME = 'hi@astraverify.com'

# Environment-specific email configuration
if ENVIRONMENT == 'staging':
    EMAIL_SMTP_SERVER = 'smtp.gmail.com'
    EMAIL_SMTP_PORT = 587
    EMAIL_USERNAME = 'hi@astraverify.com'
    STAGING_EMAIL_ENABLED = True
    STAGING_APP_PASSWORD = 'gsak aofx trxi jedl'
elif ENVIRONMENT == 'production':
    EMAIL_SMTP_SERVER = 'smtp.gmail.com'
    EMAIL_SMTP_PORT = 587
    EMAIL_USERNAME = 'hi@astraverify.com'
    STAGING_EMAIL_ENABLED = True
    PROD_APP_PASSWORD = 'mads ghsj bhdf jcjm'
else:
    # LOCAL Env
    EMAIL_SMTP_SERVER = 'smtp.gmail.com'
    EMAIL_SMTP_PORT = 587
    EMAIL_USERNAME = 'hi@astraverify.com'
    STAGING_EMAIL_ENABLED = True
    LOCAL_APP_PASSWORD = 'juek rown cptq zkpo'

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
logger.info(f"Email password configured: {bool(EMAIL_PASSWORD)}")

# Enhanced input validation
def validate_domain(domain):
    """Enhanced domain validation with security checks"""
    if not domain or not isinstance(domain, str):
        return False, "Domain parameter is required and must be a string"
    
    # Remove protocol and www if present
    domain = domain.replace('http://', '').replace('https://', '').replace('www.', '')
    
    # Check for empty domain after cleaning
    if not domain or domain.strip() == '':
        return False, "Domain cannot be empty"
    
    # Check for IP addresses (reject them)
    ip_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    if re.match(ip_pattern, domain):
        return False, "IP addresses are not valid domains"
    
    # Check for malicious patterns
    malicious_patterns = [
        r'\.\.',  # Double dots
        r'[<>"\']',  # HTML/script injection
        r'javascript:',  # JavaScript injection
        r'data:',  # Data URI injection
        r'vbscript:',  # VBScript injection
        r'file:',  # File protocol
        r'ftp:',  # FTP protocol
    ]
    
    for pattern in malicious_patterns:
        if re.search(pattern, domain, re.IGNORECASE):
            return False, f"Domain contains invalid characters or patterns"
    
    # Basic domain format validation
    domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    if not re.match(domain_pattern, domain):
        return False, "Invalid domain format"
    
    return True, domain

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
    """Get SPF record information"""
    try:
        spf_records = dns.resolver.resolve(domain, 'TXT')
        records = []
        for record in spf_records:
            record_text = record.to_text().strip('"')
            if record_text.startswith('v=spf1'):
                records.append({
                    'record': record_text,
                    'valid': True
                })
        
        if records:
            return {
                'has_spf': True,
                'records': records,
                'status': 'Valid',
                'description': f'Found {len(records)} SPF record(s)'
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
    """Get DMARC record information"""
    try:
        dmarc_domain = f"_dmarc.{domain}"
        dmarc_records = dns.resolver.resolve(dmarc_domain, 'TXT')
        records = []
        for record in dmarc_records:
            record_text = record.to_text().strip('"')
            if record_text.startswith('v=DMARC1'):
                records.append({
                    'record': record_text,
                    'valid': True
                })
        
        if records:
            return {
                'has_dmarc': True,
                'records': records,
                'status': 'Valid',
                'description': f'Found {len(records)} DMARC record(s)'
            }
        else:
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

def get_dkim_details_enhanced(domain, custom_selector=None):
    """Enhanced DKIM check using the new selector management system"""
    try:
        # Use enhanced DKIM scanner
        dkim_result = enhanced_dkim_scanner.scan_domain_dkim(domain, custom_selector)
        
        # Format result for compatibility with existing code
        formatted_records = []
        for record in dkim_result.get('records', []):
            formatted_records.append({
                'selector': record['selector'],
                'record': record['record_preview'],
                'valid': record['valid'],
                'source': record['source'],
                'priority': record['priority']
            })
        
        return {
            'has_dkim': dkim_result['has_dkim'],
            'records': formatted_records,
            'status': dkim_result['status'],
            'description': dkim_result['description'],
            'selector_analytics': dkim_result.get('selector_analytics', {}),
            'recommendations': dkim_result.get('recommendations', [])
        }
    except Exception as e:
        logger.error(f"Enhanced DKIM check failed for {domain}: {e}")
        return {
            'has_dkim': False,
            'records': [],
            'status': 'Error',
            'description': f'DKIM check failed: {str(e)}'
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

def get_security_score(mx_result, spf_result, dmarc_result, dkim_result):
    """Calculate security score with enhanced DKIM scoring"""
    score = 0
    scoring_details = {}
    
    # MX Records: 25 points
    if mx_result['has_mx']:
        score += 25
        scoring_details['mx_base'] = 25
        if len(mx_result['records']) > 1:
            score += 5
            scoring_details['mx_bonus'] = 5
    else:
        scoring_details['mx_base'] = 0
    
    # SPF Records: 25 points
    if spf_result['has_spf']:
        score += 25
        scoring_details['spf_base'] = 25
    else:
        scoring_details['spf_base'] = 0
    
    # DMARC Records: 30 points
    if dmarc_result['has_dmarc']:
        score += 30
        scoring_details['dmarc_base'] = 30
    else:
        scoring_details['dmarc_base'] = 0
    
    # DKIM Records: 20 points (enhanced scoring)
    if dkim_result['has_dkim']:
        score += 20
        scoring_details['dkim_base'] = 20
        
        # Bonus for multiple selectors
        if len(dkim_result['records']) > 1:
            score += 5
            scoring_details['dkim_bonus'] = 5
        
        # Bonus for admin-managed selectors
        admin_selectors = [r for r in dkim_result['records'] if r.get('source') == 'admin']
        if admin_selectors:
            score += 3
            scoring_details['dkim_admin_bonus'] = 3
        
        # Bonus for discovered selectors
        discovered_selectors = [r for r in dkim_result['records'] if r.get('source') == 'discovered']
        if discovered_selectors:
            score += 2
            scoring_details['dkim_discovered_bonus'] = 2
    else:
        scoring_details['dkim_base'] = 0
    
    # Cap at 100
    score = min(score, 100)
    
    return {
        'score': score,
        'scoring_details': scoring_details
    }

def get_score_grade(score):
    """Get letter grade for security score"""
    if score >= 95:
        return 'A+'
    elif score >= 90:
        return 'A'
    elif score >= 85:
        return 'A-'
    elif score >= 80:
        return 'B+'
    elif score >= 75:
        return 'B'
    elif score >= 70:
        return 'B-'
    elif score >= 65:
        return 'C+'
    elif score >= 60:
        return 'C'
    elif score >= 55:
        return 'C-'
    elif score >= 50:
        return 'D+'
    elif score >= 45:
        return 'D'
    elif score >= 40:
        return 'D-'
    else:
        return 'F'

# Main domain checking endpoint with enhanced DKIM
@app.route('/api/check', methods=['GET'])
def check_domain():
    """Main domain checking endpoint with enhanced DKIM scanning"""
    domain = request.args.get('domain')
    custom_selector = request.args.get('dkim_selector')
    progressive = request.args.get('progressive', 'false').lower() == 'true'
    
    if not domain:
        return jsonify({"error": "Domain parameter is required"}), 400
    
    # Validate domain
    is_valid, validation_result = validate_domain(domain)
    if not is_valid:
        return jsonify({"error": validation_result}), 400
    
    domain = validation_result  # Use cleaned domain
    
    logger.info(f"Starting enhanced analysis for domain: {domain}")
    if custom_selector:
        logger.info(f"Using custom DKIM selector: {custom_selector}")
    
    # Get detailed results for each check
    mx_result = get_mx_details(domain)
    spf_result = get_spf_details(domain)
    dmarc_result = get_dmarc_details(domain)
    
    if progressive:
        # Progressive mode - return early results without DKIM
        logger.info(f"Progressive mode: returning early results for {domain}")
        
        early_results = {
            "domain": domain,
            "analysis_timestamp": None,
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
                "status": "Pending",
                "description": "DKIM check will be performed separately",
                "records": []
            },
            "progressive": True
        }
        
        return jsonify(early_results)
    
    # Full analysis including enhanced DKIM
    dkim_result = get_dkim_details_enhanced(domain, custom_selector)
    
    # Detect email service provider
    email_provider = detect_email_provider(mx_result, spf_result, dkim_result)
    
    # Calculate security score
    security_score = get_security_score(mx_result, spf_result, dmarc_result, dkim_result)
    
    # Generate recommendations
    recommendations = []
    
    if not mx_result['has_mx']:
        recommendations.append({
            "type": "critical",
            "title": "Add MX Records",
            "description": "MX records are essential for email delivery. Contact your DNS provider to add MX records."
        })
    
    if not spf_result['has_spf']:
        recommendations.append({
            "type": "warning",
            "title": "Add SPF Record",
            "description": "SPF records prevent email spoofing. Add a SPF record to your DNS configuration."
        })
    
    if not dkim_result['has_dkim']:
        recommendations.append({
            "type": "info",
            "title": "Consider DKIM",
            "description": "DKIM provides email authentication. This is typically configured by your email service provider."
        })
    
    if not dmarc_result['has_dmarc']:
        recommendations.append({
            "type": "warning",
            "title": "Add DMARC Record",
            "description": "DMARC provides email authentication reporting and policy enforcement."
        })
    
    # Add DKIM-specific recommendations
    if dkim_result.get('recommendations'):
        recommendations.extend(dkim_result['recommendations'])
    
    # Compile comprehensive results
    results = {
        "domain": domain,
        "analysis_timestamp": None,
        "security_score": security_score,
        "email_provider": email_provider,
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
            "records": dkim_result['records'],
            "selector_analytics": dkim_result.get('selector_analytics', {})
        },
        "dmarc": {
            "enabled": dmarc_result['has_dmarc'],
            "status": dmarc_result['status'],
            "description": dmarc_result['description'],
            "records": dmarc_result['records']
        },
        "recommendations": recommendations,
        "progressive": False
    }
    
    # Store analysis results in Firestore
    try:
        firestore_manager.store_analysis(domain, results)
        logger.info(f"Analysis stored in Firestore for {domain}")
    except Exception as e:
        logger.warning(f"Failed to store analysis in Firestore: {e}")
    
    logger.info(f"Enhanced analysis completed for {domain}. Security score: {security_score['score']}, Provider: {email_provider}")
    return jsonify(results)

# Enhanced DKIM endpoint
@app.route('/api/check/dkim', methods=['GET'])
def complete_dkim_check():
    """Complete DKIM check for progressive mode (enhanced)"""
    domain = request.args.get('domain')
    custom_selector = request.args.get('dkim_selector')
    
    if not domain:
        return jsonify({"error": "Domain parameter is required"}), 400
    
    # Validate domain
    is_valid, validation_result = validate_domain(domain)
    if not is_valid:
        return jsonify({"error": validation_result}), 400
    
    domain = validation_result
    
    logger.info(f"Completing enhanced DKIM analysis for domain: {domain}")
    
    # Get enhanced DKIM results
    dkim_result = get_dkim_details_enhanced(domain, custom_selector)
    
    # Get other components for provider detection
    mx_result = get_mx_details(domain)
    spf_result = get_spf_details(domain)
    dmarc_result = get_dmarc_details(domain)
    
    # Detect email provider
    email_provider = detect_email_provider(mx_result, spf_result, dkim_result)
    
    # Calculate security score
    security_score = get_security_score(mx_result, spf_result, dmarc_result, dkim_result)
    
    # Generate recommendations
    recommendations = []
    if dkim_result.get('recommendations'):
        recommendations.extend(dkim_result['recommendations'])
    
    # Compile complete results for storage
    complete_results = {
        "domain": domain,
        "analysis_timestamp": None,
        "security_score": security_score,
        "email_provider": email_provider,
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
            "records": dkim_result['records'],
            "selector_analytics": dkim_result.get('selector_analytics', {})
        },
        "dmarc": {
            "enabled": dmarc_result['has_dmarc'],
            "status": dmarc_result['status'],
            "description": dmarc_result['description'],
            "records": dmarc_result['records']
        },
        "recommendations": recommendations
    }
    
    # Store analysis results in Firestore
    try:
        firestore_manager.store_analysis(domain, complete_results)
        logger.info(f"Enhanced progressive analysis stored in Firestore for {domain}")
    except Exception as e:
        logger.warning(f"Failed to store progressive analysis in Firestore: {e}")
    
    # Response data
    response_data = {
        "domain": domain,
        "dkim": dkim_result,
        "email_provider": email_provider,
        "security_score": security_score,
        "recommendations": recommendations,
        "completed": True
    }
    
    logger.info(f"Enhanced DKIM endpoint response for {domain}")
    return jsonify(response_data)

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "environment": ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "features": {
            "enhanced_dkim": True,
            "selector_management": True,
            "admin_interface": True
        }
    })

# Root endpoint
@app.route('/', methods=['GET'])
def root():
    return jsonify({
        "message": "AstraVerify Enhanced DKIM Backend",
        "version": "2.0.0",
        "environment": ENVIRONMENT,
        "endpoints": {
            "health": "/api/health",
            "check_domain": "/api/check?domain=example.com",
            "admin": "/admin",
            "admin_ui": "/admin/ui/login"
        }
    })

# Initialize admin routes
create_admin_routes(app)
create_admin_ui_routes(app)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
