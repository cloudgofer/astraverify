from datetime import datetime
from flask import Flask, request, jsonify, g
from flask_cors import CORS
import dns.resolver
import logging
import re
import os
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from firestore_config import firestore_manager
from dkim_optimizer_sync import dkim_optimizer_sync

# Import security components
from request_logger import RequestLogger
from rate_limiter import RateLimiter
from abuse_detector import AbuseDetector
from ip_blocker import IPBlocker

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

# Initialize security components
request_logger = RequestLogger()
rate_limiter = RateLimiter()
abuse_detector = AbuseDetector()
ip_blocker = IPBlocker()

# Initialize scoring system
config_loader = ConfigLoader('config')
scoring_engine = ScoringEngine(config_loader)
recommendation_engine = RecommendationEngine(config_loader)

# Environment configuration
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'local')
logger.info(f"Starting AstraVerify backend with security in {ENVIRONMENT} environment")

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

def require_admin_auth(f):
    """Decorator to require admin authentication"""
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-Admin-API-Key')
        if api_key != ADMIN_API_KEY:
            return jsonify({"error": "Admin access required"}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Security middleware
@app.before_request
def before_request():
    """Enhanced request processing with security checks"""
    g.start_time = time.time()
    
    # Get client IP and create fingerprint
    client_ip = request_logger.get_client_ip()
    fingerprint = request_logger.get_request_fingerprint()
    
    # Check if IP is blocked
    block_info = ip_blocker.is_blocked(client_ip)
    if block_info:
        g.response_status = 403
        g.response_time = (time.time() - g.start_time) * 1000
        request_logger.log_request(error=f"IP blocked: {block_info['reason']}")
        
        return jsonify({
            "error": "Access denied",
            "reason": block_info['reason'],
            "blocked_until": block_info['blocked_until'].isoformat() if block_info['blocked_until'] else None
        }), 403
    
    # Check rate limiting
    api_key = request.headers.get('X-API-Key')
    user_tier = rate_limiter.get_user_tier(api_key, client_ip)
    allowed, rate_limit_info = rate_limiter.check_rate_limit(client_ip, user_tier)
    
    if not allowed:
        g.response_status = 429
        g.response_time = (time.time() - g.start_time) * 1000
        request_logger.log_request(error="Rate limit exceeded")
        
        return jsonify({
            "error": "Rate limit exceeded",
            "retry_after": rate_limit_info['retry_after'],
            "limits": rate_limit_info['limits'],
            "current_usage": rate_limit_info['current_usage']
        }), 429
    
    # Analyze for abuse
    abuse_analysis = abuse_detector.analyze_request(fingerprint)
    
    # Take action if abuse detected
    if abuse_analysis['action_required']:
        if abuse_analysis['risk_level'] == 'critical':
            ip_blocker.block_ip(client_ip, f"Critical abuse detected: {abuse_analysis['flags']}", 'permanent')
        elif abuse_analysis['risk_level'] == 'high':
            ip_blocker.block_ip(client_ip, f"High abuse detected: {abuse_analysis['flags']}", 'extended')
        else:
            ip_blocker.block_ip(client_ip, f"Abuse detected: {abuse_analysis['flags']}", 'temporary')
    
    # Store rate limit and abuse info
    g.rate_limit_info = rate_limit_info
    g.abuse_analysis = abuse_analysis

@app.after_request
def after_request(response):
    """Log response and add rate limit headers"""
    g.response_time = (time.time() - g.start_time) * 1000
    g.response_status = response.status_code
    
    # Add rate limit headers
    if hasattr(g, 'rate_limit_info'):
        response.headers['X-RateLimit-Limit'] = str(g.rate_limit_info['limits']['requests_per_minute'])
        response.headers['X-RateLimit-Remaining'] = str(
            g.rate_limit_info['limits']['requests_per_minute'] - g.rate_limit_info['current_usage']['minute']
        )
        response.headers['X-RateLimit-Reset'] = str(int(time.time() + 60))  # Next minute
    
    # Log the request
    request_logger.log_request()
    
    return response

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "environment": ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat(),
        "security_enabled": True
    })

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
        
        # Debug logging
        logger.info(f"MX records after sorting for {domain}:")
        for record in records:
            logger.info(f"  Priority {record['priority']}: {record['server']}")
        
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
    """Get DKIM record information (optimized check)"""
    # Get MX servers for provider-specific selector prioritization
    mx_servers = []
    try:
        mx_result = get_mx_details(domain)
        if mx_result.get('has_mx'):
            mx_servers = [record['server'] for record in mx_result.get('records', [])]
    except:
        pass
    
    # Use optimized DKIM checker
    result = dkim_optimizer_sync.get_dkim_details_optimized(domain, custom_selector, mx_servers)
    
    # Remove internal timing info from result
    if 'check_time' in result:
        del result['check_time']
    
    return result

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
    """
    Calculate comprehensive security score with bonus points.
    
    Base Scoring (100 points total):
    - MX Records: 25 points (essential for email delivery)
    - SPF Records: 25 points (prevents email spoofing)
    - DMARC Records: 30 points (authentication reporting)
    - DKIM Records: 20 points (email authentication)
    
    Bonus Points (up to 10 additional points):
    - Multiple MX records: +2 points (redundancy)
    - Strong SPF policy: +1-2 points (-all > ~all > ?all)
    - Strict DMARC policy: +1-2 points (p=reject > p=quarantine)
    - Multiple DKIM selectors: +2 points (diversity) - only for non-Google providers
    - 100% DMARC coverage: +1 point (pct=100)
    """
    score = 0
    max_score = 100
    bonus_points = 0
    max_bonus = 10
    scoring_details = {}
    
    # Base scoring (MX: 25, SPF: 25, DMARC: 30, DKIM: 20)
    if mx_result['has_mx']:
        # Check if MX records are actually functional
        functional_mx = False
        for record in mx_result['records']:
            server = record.get('server', '')
            # Skip non-functional servers like "." or empty strings
            if server and server != '.' and server != '':
                functional_mx = True
                break
        
        if functional_mx:
            score += 25
            scoring_details['mx_base'] = 25
            # Bonus for multiple MX records (redundancy)
            if len(mx_result['records']) > 1:
                bonus_points += 2
                scoring_details['mx_bonus'] = 2
            else:
                scoring_details['mx_bonus'] = 0
        else:
            # MX records exist but are not functional
            scoring_details['mx_base'] = 0
            scoring_details['mx_bonus'] = 0
    else:
        scoring_details['mx_base'] = 0
        scoring_details['mx_bonus'] = 0
    
    if spf_result['has_spf']:
        score += 25
        scoring_details['spf_base'] = 25
        # Bonus for strong SPF policy
        spf_bonus = 0
        for record in spf_result['records']:
            if '-all' in record['record']:
                spf_bonus += 2  # Strongest policy
            elif '~all' in record['record']:
                spf_bonus += 1  # Medium policy
            elif '?all' in record['record']:
                spf_bonus += 0.5  # Weakest policy
        bonus_points += spf_bonus
        scoring_details['spf_bonus'] = spf_bonus
    else:
        scoring_details['spf_base'] = 0
        scoring_details['spf_bonus'] = 0
    
    if dmarc_result['has_dmarc']:
        score += 30
        scoring_details['dmarc_base'] = 30
        # Bonus for strong DMARC policy
        dmarc_bonus = 0
        for record in dmarc_result['records']:
            if 'p=reject' in record['record']:
                dmarc_bonus += 2  # Strictest policy
            elif 'p=quarantine' in record['record']:
                dmarc_bonus += 1  # Medium policy
            if 'pct=100' in record['record']:
                dmarc_bonus += 1  # 100% coverage
        bonus_points += dmarc_bonus
        scoring_details['dmarc_bonus'] = dmarc_bonus
    else:
        scoring_details['dmarc_base'] = 0
        scoring_details['dmarc_bonus'] = 0
    
    if dkim_result['has_dkim']:
        score += 20
        scoring_details['dkim_base'] = 20
        # Bonus for multiple DKIM selectors (only for non-Google providers)
        provider = detect_email_provider(mx_result, spf_result, dkim_result)
        if len(dkim_result['records']) > 1 and provider != "Google Workspace":
            bonus_points += 2
            scoring_details['dkim_bonus'] = 2
        else:
            scoring_details['dkim_bonus'] = 0
    else:
        scoring_details['dkim_base'] = 0
        scoring_details['dkim_bonus'] = 0
    
    # Apply bonus points (capped at max_bonus)
    final_score = min(score + bonus_points, max_score)
    
    # Determine grade and status
    if final_score >= 90:
        grade = 'A'
        status = 'Excellent'
    elif final_score >= 75:
        grade = 'B'
        status = 'Good'
    elif final_score >= 50:
        grade = 'C'
        status = 'Fair'
    elif final_score >= 25:
        grade = 'D'
        status = 'Poor'
    else:
        grade = 'F'
        status = 'Very Poor'
    
    return {
        'score': round(final_score, 1),
        'grade': grade,
        'status': status,
        'max_score': max_score,
        'base_score': score,
        'bonus_points': round(bonus_points, 1),
        'max_bonus': max_bonus,
        'scoring_details': scoring_details
    }

# Main domain checking endpoint
@app.route('/api/check', methods=['GET'])
def check_domain():
    """Main domain checking endpoint with security"""
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
        recommendations = recommendation_engine.generate_recommendations(component_scores, mx_result, spf_result, dmarc_result, {'has_dkim': False, 'records': []})
        
        early_results = {
            "domain": domain,
            "analysis_timestamp": None,
            "security_score": total_score,
            "email_provider": "Unknown",
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
    recommendations = recommendation_engine.generate_recommendations(component_scores, mx_result, spf_result, dmarc_result, dkim_result)
    
    # Compile comprehensive results
    results = {
        "domain": domain,
        "analysis_timestamp": None,
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

# Admin endpoints for security management
@app.route('/api/admin/blocked-ips', methods=['GET'])
@require_admin_auth
def get_blocked_ips():
    """Admin endpoint to view blocked IPs"""
    return jsonify({
        'blocked_ips': ip_blocker.get_blocked_ips(),
        'total_blocked': len(ip_blocker.get_blocked_ips()),
        'statistics': ip_blocker.get_block_statistics()
    })

@app.route('/api/admin/unblock-ip/<ip>', methods=['POST'])
@require_admin_auth
def unblock_ip(ip):
    """Admin endpoint to unblock an IP"""
    success = ip_blocker.unblock_ip(ip)
    return jsonify({
        'success': success,
        'message': f"IP {ip} {'unblocked' if success else 'not found'}"
    })

@app.route('/api/admin/block-ip/<ip>', methods=['POST'])
@require_admin_auth
def block_ip(ip):
    """Admin endpoint to block an IP"""
    data = request.get_json() or {}
    reason = data.get('reason', 'Manual block')
    level = data.get('level', 'temporary')
    
    success = ip_blocker.block_ip(ip, reason, level)
    return jsonify({
        'success': success,
        'message': f"IP {ip} {'blocked' if success else 'failed to block'}"
    })

@app.route('/api/admin/ip-analytics/<ip>', methods=['GET'])
@require_admin_auth
def get_ip_analytics(ip):
    """Admin endpoint to get IP analytics"""
    hours = request.args.get('hours', 24, type=int)
    analytics = firestore_manager.get_ip_analytics(ip, hours)
    abuse_score = abuse_detector.ip_scores.get(ip, 0)
    
    return jsonify({
        'ip': ip,
        'analytics': analytics,
        'abuse_score': abuse_score,
        'risk_level': abuse_detector._get_risk_level(abuse_score),
        'is_blocked': bool(ip_blocker.is_blocked(ip)),
        'block_info': ip_blocker.get_block_info(ip)
    })

@app.route('/api/admin/security-dashboard', methods=['GET'])
@require_admin_auth
def security_dashboard():
    """Admin dashboard for security monitoring"""
    return jsonify({
        'rate_limiting': {
            'total_requests_today': firestore_manager.get_daily_request_count(),
            'rate_limited_requests': firestore_manager.get_rate_limited_count(),
            'top_ips': firestore_manager.get_top_requesting_ips()
        },
        'abuse_detection': {
            'blocked_ips_count': len(ip_blocker.get_blocked_ips()),
            'high_risk_ips': len([ip for ip, score in abuse_detector.ip_scores.items() if score >= 30]),
            'block_statistics': ip_blocker.get_block_statistics()
        },
        'system_health': {
            'environment': ENVIRONMENT,
            'security_enabled': True,
            'redis_available': rate_limiter.redis_client is not None
        }
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
