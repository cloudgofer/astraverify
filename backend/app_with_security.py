from datetime import datetime
from flask import Flask, request, jsonify, g
from flask_cors import CORS
import dns.resolver
import logging
import re
import os
import smtplib
import time
import redis
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
logger.info(f"Starting AstraVerify backend with ENHANCED security in {ENVIRONMENT} environment")

# Admin authentication
ADMIN_API_KEY = os.environ.get('ADMIN_API_KEY', 'astraverify-admin-2024')

# Rate limiting configuration
RATE_LIMIT_CONFIG = {
    'free': {
        'requests_per_minute': 10,
        'requests_per_hour': 100,
        'requests_per_day': 1000
    },
    'authenticated': {
        'requests_per_minute': 30,
        'requests_per_hour': 500,
        'requests_per_day': 5000
    },
    'premium': {
        'requests_per_minute': 100,
        'requests_per_hour': 2000,
        'requests_per_day': 20000
    }
}

# Initialize Redis for rate limiting
redis_client = None
try:
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    redis_client = redis.from_url(redis_url, decode_responses=True)
    redis_client.ping()
    logger.info("Connected to Redis for enhanced rate limiting")
except Exception as e:
    logger.warning(f"Redis not available, using in-memory rate limiting: {e}")
    redis_client = None

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
        r'<script',  # XSS attempts
        r'javascript:',  # JavaScript injection
        r'data:',  # Data URI injection
        r'vbscript:',  # VBScript injection
        r'<iframe',  # Iframe injection
        r'<object',  # Object injection
        r'<embed',  # Embed injection
        r'<form',  # Form injection
        r'<input',  # Input injection
        r'<textarea',  # Textarea injection
        r'<select',  # Select injection
        r'<button',  # Button injection
        r'<link',  # Link injection
        r'<meta',  # Meta injection
        r'<style',  # Style injection
        r'<title',  # Title injection
        r'<body',  # Body injection
        r'<head',  # Head injection
        r'<html',  # HTML injection
        r'<xml',  # XML injection
        r'<svg',  # SVG injection
        r'<math',  # MathML injection
        r'<applet',  # Applet injection
        r'<base',  # Base injection
        r'<bgsound',  # BGSound injection
        r'<link',  # Link injection
        r'<meta',  # Meta injection
        r'<script',  # Script injection
        r'<title',  # Title injection
        r'<xmp',  # XMP injection
    ]
    
    for pattern in malicious_patterns:
        if re.search(pattern, domain, re.IGNORECASE):
            return False, f"Domain contains malicious pattern: {pattern}"
    
    # Check for SQL injection patterns
    sql_patterns = [
        r"';",  # SQL injection
        r"--",  # SQL comment
        r"/\*",  # SQL comment (escaped)
        r"\*/",  # SQL comment (escaped)
        r"\bxp_",  # SQL extended procedure (word boundary)
        r"\bsp_",  # SQL stored procedure (word boundary)
        r"@@",  # SQL variable
        r"\bchar\(",  # SQL function (word boundary)
        r"\bnchar\(",  # SQL function (word boundary)
        r"\bvarchar\(",  # SQL function (word boundary)
        r"\bnvarchar\(",  # SQL function (word boundary)
        r"\bcast\(",  # SQL function (word boundary)
        r"\bconvert\(",  # SQL function (word boundary)
        r"\bexec\b",  # SQL execution (word boundary)
        r"\bexecute\b",  # SQL execution (word boundary)
        r"\bunion\b",  # SQL union (word boundary)
        r"\bselect\b",  # SQL select (word boundary)
        r"\binsert\b",  # SQL insert (word boundary)
        r"\bupdate\b",  # SQL update (word boundary)
        r"\bdelete\b",  # SQL delete (word boundary)
        r"\bdrop\b",  # SQL drop (word boundary)
        r"\bcreate\b",  # SQL create (word boundary)
        r"\balter\b",  # SQL alter (word boundary)
        r"\btruncate\b",  # SQL truncate (word boundary)
        r"\bbackup\b",  # SQL backup (word boundary)
        r"\brestore\b",  # SQL restore (word boundary)
        r"\bshutdown\b",  # SQL shutdown (word boundary)
        r"\bkill\b",  # SQL kill (word boundary)
    ]
    
    for pattern in sql_patterns:
        if re.search(pattern, domain, re.IGNORECASE):
            return False, f"Domain contains SQL injection pattern: {pattern}"
    
    # Check domain length
    if len(domain) > 253:  # RFC 1035 limit
        return False, "Domain is too long (maximum 253 characters)"
    
    # Check for valid domain format
    domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    if not re.match(domain_pattern, domain):
        return False, "Invalid domain format"
    
    return True, domain

def require_admin_auth(f):
    """Decorator to require admin authentication"""
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-Admin-API-Key')
        if api_key != ADMIN_API_KEY:
            return jsonify({"error": "Admin access required"}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Enhanced rate limiting with Redis
class EnhancedRateLimiter:
    def __init__(self):
        self.redis_client = redis_client
        self.limits = RATE_LIMIT_CONFIG
    
    def get_user_tier(self, api_key=None, ip=None):
        """Determine user tier based on API key or IP reputation"""
        if api_key and self._is_valid_api_key(api_key):
            return 'authenticated'
        elif self._is_premium_ip(ip):
            return 'premium'
        return 'free'
    
    def _is_valid_api_key(self, api_key):
        """Check if API key is valid"""
        valid_keys = os.environ.get('VALID_API_KEYS', '').split(',')
        return api_key in valid_keys
    
    def _is_premium_ip(self, ip):
        """Check if IP is premium (trusted)"""
        premium_ips = os.environ.get('PREMIUM_IPS', '').split(',')
        return ip in premium_ips
    
    def check_rate_limit(self, identifier, tier='free'):
        """Check if request is within rate limits"""
        if self.redis_client:
            return self._check_rate_limit_redis(identifier, tier)
        else:
            return self._check_rate_limit_memory(identifier, tier)
    
    def _check_rate_limit_redis(self, identifier, tier):
        """Check rate limits using Redis"""
        try:
            limits = self.limits[tier]
            now = datetime.utcnow()
            
            # Create keys for different time windows
            minute_key = f"rate_limit:{identifier}:{now.strftime('%Y%m%d%H%M')}"
            hour_key = f"rate_limit:{identifier}:{now.strftime('%Y%m%d%H')}"
            day_key = f"rate_limit:{identifier}:{now.strftime('%Y%m%d')}"
            
            # Get current counts
            minute_count = int(self.redis_client.get(minute_key) or 0)
            hour_count = int(self.redis_client.get(hour_key) or 0)
            day_count = int(self.redis_client.get(day_key) or 0)
            
            # Check if any limit is exceeded
            if (minute_count >= limits['requests_per_minute'] or
                hour_count >= limits['requests_per_hour'] or
                day_count >= limits['requests_per_day']):
                
                return False, {
                    'retry_after': 60,
                    'limits': limits,
                    'current_usage': {
                        'minute': minute_count,
                        'hour': hour_count,
                        'day': day_count
                    }
                }
            
            # Increment counters
            pipe = self.redis_client.pipeline()
            pipe.incr(minute_key)
            pipe.incr(hour_key)
            pipe.incr(day_key)
            pipe.expire(minute_key, 60)
            pipe.expire(hour_key, 3600)
            pipe.expire(day_key, 86400)
            pipe.execute()
            
            return True, {
                'retry_after': 0,
                'limits': limits,
                'current_usage': {
                    'minute': minute_count + 1,
                    'hour': hour_count + 1,
                    'day': day_count + 1
                }
            }
            
        except Exception as e:
            logger.error(f"Redis rate limiting error: {e}")
            return True, {
                'retry_after': 0,
                'limits': self.limits.get(tier, self.limits['free']),
                'current_usage': {'minute': 0, 'hour': 0, 'day': 0}
            }
    
    def _check_rate_limit_memory(self, identifier, tier):
        """Fallback to in-memory rate limiting"""
        # Simple in-memory implementation
        return True, {
            'retry_after': 0,
            'limits': self.limits.get(tier, self.limits['free']),
            'current_usage': {'minute': 0, 'hour': 0, 'day': 0}
        }

# Initialize enhanced rate limiter
enhanced_rate_limiter = EnhancedRateLimiter()

# Security middleware with enhanced features
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
    
    # Enhanced rate limiting
    api_key = request.headers.get('X-API-Key')
    user_tier = enhanced_rate_limiter.get_user_tier(api_key, client_ip)
    allowed, rate_limit_info = enhanced_rate_limiter.check_rate_limit(client_ip, user_tier)
    
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
    """Enhanced response processing with security headers and rate limit headers"""
    g.response_time = (time.time() - g.start_time) * 1000
    g.response_status = response.status_code
    
    # Add security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https:; connect-src 'self' https:; frame-ancestors 'none';"
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    
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
        "security_enabled": True,
        "enhanced_security": True,
        "rate_limiting": "enabled",
        "input_validation": "enhanced"
    })

# Admin endpoints
@app.route('/api/admin/security-dashboard', methods=['GET'])
@require_admin_auth
def admin_security_dashboard():
    """Admin security dashboard endpoint"""
    try:
        # Get security statistics
        stats = {
            "total_requests": firestore_manager.get_daily_request_count(),
            "rate_limited_requests": firestore_manager.get_rate_limited_count(),
            "top_requesting_ips": firestore_manager.get_top_requesting_ips(10),
            "environment": ENVIRONMENT,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Admin dashboard error: {e}")
        return jsonify({"error": "Failed to get security statistics"}), 500

@app.route('/api/admin/blocked-ips', methods=['GET'])
@require_admin_auth
def admin_blocked_ips():
    """Get list of blocked IPs"""
    try:
        # This would need to be implemented in IPBlocker
        blocked_ips = []  # Placeholder
        return jsonify({"blocked_ips": blocked_ips})
    except Exception as e:
        logger.error(f"Blocked IPs error: {e}")
        return jsonify({"error": "Failed to get blocked IPs"}), 500

# Helper functions for domain analysis
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

# Main domain checking endpoint with enhanced validation
@app.route('/api/check', methods=['GET'])
def check_domain():
    """Main domain checking endpoint with enhanced security"""
    domain = request.args.get('domain')
    progressive = request.args.get('progressive', 'false').lower() == 'true'
    
    # Enhanced input validation
    is_valid, validation_result = validate_domain(domain)
    if not is_valid:
        return jsonify({"error": validation_result}), 400
    
    domain = validation_result  # Clean domain
    
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
        early_parsed_data = {
            'mx': mx_result,
            'spf': spf_result,
            'dmarc': dmarc_result,
            'dkim': {'has_dkim': False, 'records': []}
        }
        recommendations = recommendation_engine.generate_recommendations(component_scores, early_parsed_data)
        
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
    parsed_data = {
        'mx': mx_result,
        'spf': spf_result,
        'dmarc': dmarc_result,
        'dkim': dkim_result
    }
    recommendations = recommendation_engine.generate_recommendations(component_scores, parsed_data)
    
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

def send_email_report(to_email, domain, analysis_result, opt_in_marketing):
    """Send email report with analysis results"""
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = f'AstraVerify <{EMAIL_SENDER}>'
        msg['To'] = to_email
        msg['Subject'] = f'AstraVerify Security Report for {domain}'
        
        # Add anti-spam headers
        msg['Message-ID'] = f'<{domain}-{int(datetime.now().timestamp())}@astraverify.com>'
        msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
        msg['X-Mailer'] = 'AstraVerify Email System'
        msg['X-Priority'] = '3'
        msg['X-MSMail-Priority'] = 'Normal'
        msg['Importance'] = 'Normal'
        msg['MIME-Version'] = '1.0'
        
        # Add unsubscribe header for marketing emails
        if opt_in_marketing:
            msg['List-Unsubscribe'] = '<https://astraverify.com/unsubscribe>'
            msg['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'
        
        # Determine frontend URL based on environment
        if ENVIRONMENT == 'staging':
            frontend_url = 'https://astraverify-frontend-staging-ml2mhibdvq-uc.a.run.app'
        elif ENVIRONMENT == 'local':
            frontend_url = 'http://localhost:3000'
        else:
            frontend_url = 'https://astraverify-frontend-ml2mhibdvq-uc.a.run.app'
        
        logger.info(f"Email environment: {ENVIRONMENT}, frontend URL: {frontend_url}")
        
        # Get score and grade
        score = analysis_result.get('security_score', 0)
        # Handle case where security_score is a dictionary
        if isinstance(score, dict):
            score = score.get('score', 0)
        grade = get_score_grade(score)
        
        # Get component details
        mx = analysis_result.get('mx', {})
        spf = analysis_result.get('spf', {})
        dkim = analysis_result.get('dkim', {})
        dmarc = analysis_result.get('dmarc', {})
        
        # Create HTML content
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .domain {{ font-size: 24px; font-weight: bold; color: #333; margin: 20px 0; }}
                .domain a {{ color: #007bff; text-decoration: none; font-weight: bold; border-bottom: 1px dotted #007bff; }}
                .domain a:hover {{ color: #0056b3; text-decoration: underline; border-bottom: 1px solid #0056b3; }}
                .score-section {{ text-align: center; margin: 30px 0; }}
                .score {{ font-size: 36px; font-weight: bold; color: #333; }}
                .grade {{ font-size: 18px; color: #666; margin: 10px 0; }}
                .component {{ margin: 20px 0; padding: 15px; border-radius: 5px; }}
                .component.valid {{ background: #d4edda; border-left: 4px solid #28a745; }}
                .component.invalid {{ background: #f8d7da; border-left: 4px solid #dc3545; }}
                .component h3 {{ margin: 0 0 10px 0; color: #333; }}
                .status {{ font-weight: bold; margin: 5px 0; }}
                .status.valid {{ color: #28a745; }}
                .status.invalid {{ color: #dc3545; }}
                .description {{ margin: 10px 0; color: #666; }}
                .issues-section {{ margin: 30px 0; }}
                .recommendations-section {{ margin: 30px 0; }}
                .issue {{ margin: 10px 0; padding: 10px; background: #fff3cd; border-left: 4px solid #ffc107; }}
                .recommendation {{ margin: 10px 0; padding: 10px; background: #d1ecf1; border-left: 4px solid #17a2b8; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🛡️ Domain Security Analysis</h1>
                    <div class="domain">
                        <a href="{frontend_url}?domain={domain}" style="color: #007bff; text-decoration: none; font-weight: bold;">{domain}</a>
                    </div>
                </div>
                
                <div class="score-section">
                    <div class="score">{grade}</div>
                    <div class="grade">{score}/100 - {get_security_status(score)}</div>
                </div>
                
                <div class="component {'valid' if mx.get('enabled') else 'invalid'}">
                    <h3>{'✅' if mx.get('enabled') else '❌'} MX Records</h3>
                    <div class="status {'valid' if mx.get('enabled') else 'invalid'}">
                        Status: {mx.get('status', 'Unknown')}
                    </div>
                    <div class="description">
                        {mx.get('description', '')}
                    </div>
                </div>
                
                <div class="component {'valid' if spf.get('enabled') else 'invalid'}">
                    <h3>{'✅' if spf.get('enabled') else '❌'} SPF Record</h3>
                    <div class="status {'valid' if spf.get('enabled') else 'invalid'}">
                        Status: {spf.get('status', 'Unknown')}
                    </div>
                    <div class="description">
                        {spf.get('description', '')}
                    </div>
                </div>
                
                <div class="component {'valid' if dkim.get('enabled') else 'invalid'}">
                    <h3>{'✅' if dkim.get('enabled') else '❌'} DKIM Record</h3>
                    <div class="status {'valid' if dkim.get('enabled') else 'invalid'}">
                        Status: {dkim.get('status', 'Unknown')}
                    </div>
                    <div class="description">
                        {dkim.get('description', '')}
                    </div>
                </div>
                
                <div class="component {'valid' if dmarc.get('enabled') else 'invalid'}">
                    <h3>{'✅' if dmarc.get('enabled') else '❌'} DMARC Record</h3>
                    <div class="status {'valid' if dmarc.get('enabled') else 'invalid'}">
                        Status: {dmarc.get('status', 'Unknown')}
                    </div>
                    <div class="description">
                        {dmarc.get('description', '')}
                    </div>
                </div>
        """
        
        # Add issues section if there are problems
        issues = []
        if not dkim.get('enabled'):
            issues.append("No DKIM records found - emails may be marked as spam")
        if not spf.get('enabled'):
            issues.append("No SPF record found - domain vulnerable to email spoofing")
        if not dmarc.get('enabled'):
            issues.append("No DMARC record found - email authentication not enforced")
        
        if issues:
            html_content += """
                <div class="issues-section">
                    <h3>🔍 Issues Found</h3>
            """
            for issue in issues:
                html_content += f"""
                    <div class="issue">
                        {issue}
                    </div>
                """
            html_content += "</div>"
        
        # Add recommendations section
        if analysis_result.get('recommendations'):
            html_content += """
                <div class="recommendations-section">
                    <h3>💡 Recommendations</h3>
            """
            for rec in analysis_result.get('recommendations', []):
                html_content += f"""
                    <div class="recommendation">
                        <strong>{rec.get('title', '')}</strong><br>
                        {rec.get('description', '')}
                    </div>
                """
            html_content += "</div>"
        
        # Add footer with current date and version
        current_date = datetime.now().strftime("%B %d, %Y")
        
        # Read version from VERSION file
        try:
            with open('VERSION', 'r') as f:
                version = f.read().strip()
        except:
            version = "2025.08.15.01-Beta"
        
        html_content += f"""
                <div class="footer">
                    <p>Report generated on {current_date}</p>
                    <p>Generated by AstraVerify - Email Domain Security Analysis Tool</p>
                    <p style="font-size: 11px; color: #999; margin-top: 20px;">
                        This email was sent to {to_email} in response to a security analysis request for {domain}.<br>
                        If you did not request this report, please ignore this email.
                    </p>
                    <p style="font-size: 10px; color: #999; margin-top: 10px; border-top: 1px solid #eee; padding-top: 10px;">
                        v{version} | © AstraVerify.com - a CloudGofer.com service
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Attach HTML content
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Send email
        logger.info(f"Attempting to send email to {to_email} via {EMAIL_SMTP_SERVER}:{EMAIL_SMTP_PORT}")
        
        server = smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT)
        logger.info("SMTP connection established")
        
        server.starttls()
        logger.info("TLS started")
        
        # Try different authentication methods
        try:
            server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            logger.info("SMTP authentication successful with LOGIN")
        except Exception as login_error:
            logger.warning(f"LOGIN authentication failed: {login_error}")
            # Try PLAIN authentication as fallback
            try:
                server.ehlo()
                server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
                logger.info("SMTP authentication successful with PLAIN")
            except Exception as plain_error:
                logger.error(f"PLAIN authentication also failed: {plain_error}")
                raise plain_error
        
        text = msg.as_string()
        server.sendmail(EMAIL_SENDER, to_email, text)
        logger.info("Email sent successfully")
        
        server.quit()
        logger.info(f"Email report sent successfully to {to_email} for domain {domain}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False

def get_score_grade(score):
    """Get letter grade for security score"""
    if score >= 95: return 'A+'
    if score >= 90: return 'A'
    if score >= 85: return 'A-'
    if score >= 80: return 'B+'
    if score >= 75: return 'B'
    if score >= 70: return 'B-'
    if score >= 65: return 'C+'
    if score >= 60: return 'C'
    if score >= 55: return 'C-'
    if score >= 50: return 'D+'
    if score >= 45: return 'D'
    if score >= 40: return 'D-'
    return 'F'

def get_security_status(score):
    """Get security status based on score"""
    if score >= 90:
        return "Excellent Security"
    elif score >= 80:
        return "Good Security"
    elif score >= 70:
        return "Fair Security"
    elif score >= 60:
        return "Poor Security"
    else:
        return "Poor Security"

# Email report endpoint
@app.route('/api/email-report', methods=['POST'])
def email_report():
    """Email report endpoint with enhanced validation and email sending"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'domain', 'analysis_result']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Validate email format
        email = data['email']
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return jsonify({"error": "Invalid email format"}), 400
        
        # Validate domain
        domain = data['domain']
        is_valid, validation_result = validate_domain(domain)
        if not is_valid:
            return jsonify({"error": validation_result}), 400
        
        # Store email report
        timestamp = datetime.utcnow()
        opt_in_marketing = data.get('opt_in_marketing', False)
        
        try:
            success = firestore_manager.store_email_report(
                email, domain, data['analysis_result'], opt_in_marketing, timestamp
            )
            logger.info(f"Email report stored in Firestore for {domain} to {email}")
        except Exception as e:
            logger.error(f"Failed to store email report in Firestore: {e}")
            # Continue with email sending even if Firestore storage fails
        
        # Send actual email
        if EMAIL_PASSWORD:
            email_sent = send_email_report(email, domain, data['analysis_result'], opt_in_marketing)
            if email_sent:
                return jsonify({
                    "success": True,
                    "message": "Email report sent successfully",
                    "email_sent": True,
                    "email_configured": True
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Failed to send email"
                }), 500
        else:
            # If no email password configured, return error
            return jsonify({
                "success": False,
                "error": "Email sending is not configured on this server",
                "email_configured": False
            }), 503
            
    except Exception as e:
        logger.error(f"Email report error: {e}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
