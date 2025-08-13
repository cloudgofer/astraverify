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
from dkim_optimizer_sync import dkim_optimizer_sync

# Configure DNS resolver for better reliability
dns.resolver.default_resolver = dns.resolver.Resolver(configure=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Environment configuration
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'production')
logger.info(f"Starting AstraVerify backend in {ENVIRONMENT} environment")

# Admin authentication
ADMIN_API_KEY = os.environ.get('ADMIN_API_KEY', 'astraverify-admin-2024')

# Email configuration
EMAIL_SENDER = 'hi@astraverify.com'
EMAIL_SMTP_SERVER = 'smtp.gmail.com'  # Gmail SMTP server
EMAIL_SMTP_PORT = 587
EMAIL_USERNAME = 'hi@astraverify.com'

# Environment-specific email configuration
if ENVIRONMENT == 'staging':
    # STAGE Env: gsak aofx trxi jedl
    EMAIL_SMTP_SERVER = 'smtp.gmail.com'
    EMAIL_SMTP_PORT = 587
    EMAIL_USERNAME = 'hi@astraverify.com'
    STAGING_EMAIL_ENABLED = True
    STAGING_APP_PASSWORD = 'gsak aofx trxi jedl'
elif ENVIRONMENT == 'production':
    # PROD Env: mads ghsj bhdf jcjm
    EMAIL_SMTP_SERVER = 'smtp.gmail.com'
    EMAIL_SMTP_PORT = 587
    EMAIL_USERNAME = 'hi@astraverify.com'
    STAGING_EMAIL_ENABLED = True
    PROD_APP_PASSWORD = 'mads ghsj bhdf jcjm'
else:
    # LOCAL Env: juek rown cptq zkpo
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
    
    # Use environment-specific app passwords
    if ENVIRONMENT == 'staging':
        logger.info("Using STAGING app password")
        return STAGING_APP_PASSWORD
    elif ENVIRONMENT == 'production':
        logger.info("Using PRODUCTION app password")
        return PROD_APP_PASSWORD
    else:
        logger.info("Using LOCAL app password")
        return LOCAL_APP_PASSWORD
    
    # Fallback to GCP Secret Manager (if needed)
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
        else:
            frontend_url = 'https://astraverify.com'
        
        # Get score and grade
        score = analysis_result.get('security_score', {}).get('score', 0)
        grade = get_score_grade(score)
        
        # Get component details
        mx = analysis_result.get('mx', {})
        spf = analysis_result.get('spf', {})
        dkim = analysis_result.get('dkim', {})
        dmarc = analysis_result.get('dmarc', {})
        
        # Get scoring details
        scoring_details = analysis_result.get('security_score', {}).get('scoring_details', {})
        
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
                .score-detail {{ margin: 5px 0; }}
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
                    <div class="score-detail">
                        Score: {scoring_details.get('mx_base', 0)}/20
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
                    <div class="score-detail">
                        Score: {scoring_details.get('spf_base', 0)}/25
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
                    <div class="score-detail">
                        Score: {scoring_details.get('dkim_base', 0)}/20
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
                    <div class="score-detail">
                        Score: {scoring_details.get('dmarc_base', 0)}/30
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
        
        # Add footer with current date
        current_date = datetime.now().strftime("%B %d, %Y")
        
        html_content += f"""
                <div class="footer">
                    <p>Report generated on {current_date}</p>
                    <p>Generated by AstraVerify - Email Domain Security Analysis Tool</p>
                    <p style="font-size: 11px; color: #999; margin-top: 20px;">
                        This email was sent to {to_email} in response to a security analysis request for {domain}.<br>
                        If you did not request this report, please ignore this email.
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

@app.route('/api/check', methods=['GET'])
def check_domain():
    domain = request.args.get('domain')
    custom_selector = request.args.get('dkim_selector')  # New parameter for custom DKIM selector
    progressive = request.args.get('progressive', 'false').lower() == 'true'
    
    if not domain:
        return jsonify({"error": "Domain parameter is required"}), 400
    
    # Remove protocol if present
    domain = domain.replace('http://', '').replace('https://', '').replace('www.', '')
    
    logger.info(f"Starting comprehensive analysis for domain: {domain}")
    if custom_selector:
        logger.info(f"Using custom DKIM selector: {custom_selector}")
    
    # Get detailed results for each check
    mx_result = get_mx_details(domain)
    spf_result = get_spf_details(domain)
    dmarc_result = get_dmarc_details(domain)
    
    # For progressive mode, return early results
    if progressive:

        # Calculate partial security score without DKIM
        partial_dkim_result = {
            'has_dkim': False,
            'records': [],
            'status': 'Checking...',
            'description': 'Comprehensive DKIM check in progress...'
        }
        
        # Calculate partial security score
        try:
            partial_security_score = get_security_score(mx_result, spf_result, dmarc_result, partial_dkim_result)
            logger.info(f"Partial security score calculated: {partial_security_score}")
        except Exception as e:
            logger.error(f"Error calculating partial security score: {e}")
            # Fallback to a basic score
            partial_security_score = {
                "score": 0,
                "base_score": 0,
                "bonus_points": 0,
                "grade": "F",
                "status": "Unknown",
                "scoring_details": {
                    "mx_base": 0,
                    "mx_bonus": 0,
                    "spf_base": 0,
                    "spf_bonus": 0,
                    "dkim_base": 0,
                    "dkim_bonus": 0,
                    "dmarc_base": 0,
                    "dmarc_bonus": 0
                }
            }
        
        early_results = {
            "domain": domain,
            "analysis_timestamp": None,
            "security_score": {
                "score": 75,  # Default score for progressive mode
                "base_score": 75,
                "bonus_points": 0,
                "grade": "C",
                "status": "Partial",
                "scoring_details": {
                    "mx_base": 25,
                    "mx_bonus": 0,
                    "spf_base": 0,
                    "spf_bonus": 0,
                    "dkim_base": 0,
                    "dkim_bonus": 0,
                    "dmarc_base": 30,
                    "dmarc_bonus": 0
                }
            },
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
            "message": "Initial results ready, DKIM check in progress..."
        }
        return jsonify(early_results)
    
    # Full analysis including DKIM
    dkim_result = get_dkim_details(domain, custom_selector)
    
    # Detect email service provider
    email_provider = detect_email_provider(mx_result, spf_result, dkim_result)
    
    # Calculate security score
    security_score = get_security_score(mx_result, spf_result, dmarc_result, dkim_result)
    
    # Compile comprehensive results
    results = {
        "domain": domain,
        "analysis_timestamp": None,  # Will be set by frontend
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
            "records": dkim_result['records']
        },
        "dmarc": {
            "enabled": dmarc_result['has_dmarc'],
            "status": dmarc_result['status'],
            "description": dmarc_result['description'],
            "records": dmarc_result['records']
        },
        "recommendations": []
    }
    
    # Generate enhanced recommendations based on email provider
    if not mx_result['has_mx']:
        results["recommendations"].append({
            "type": "critical",
            "title": "Add MX Records",
            "description": "MX records are essential for email delivery. Contact your DNS provider to add MX records."
        })
    elif len(mx_result['records']) == 1:
        results["recommendations"].append({
            "type": "info",
            "title": "Consider Multiple MX Records",
            "description": "Adding secondary MX records improves email delivery reliability and redundancy."
        })
    
    if not spf_result['has_spf']:
        if email_provider == "Google Workspace":
            results["recommendations"].append({
                "type": "important",
                "title": "Add SPF Record",
                "description": "SPF records help prevent email spoofing. Add a TXT record with 'v=spf1 include:_spf.google.com ~all' for Google Workspace."
            })
        elif email_provider == "Microsoft 365":
            results["recommendations"].append({
                "type": "important",
                "title": "Add SPF Record",
                "description": "SPF records help prevent email spoofing. Add a TXT record with 'v=spf1 include:spf.protection.outlook.com ~all' for Microsoft 365."
            })
        else:
            results["recommendations"].append({
                "type": "important",
                "title": "Add SPF Record",
                "description": "SPF records help prevent email spoofing. Contact your email service provider for the correct SPF record."
            })
    elif any('~all' in r['record'] for r in spf_result['records']):
        results["recommendations"].append({
            "type": "info",
            "title": "Strengthen SPF Policy",
            "description": "Consider changing '~all' to '-all' for stronger spoofing protection."
        })
    
    if not dmarc_result['has_dmarc']:
        results["recommendations"].append({
            "type": "important",
            "title": "Add DMARC Record",
            "description": "DMARC records provide email authentication reporting. Add a TXT record at _dmarc.yourdomain.com with 'v=DMARC1; p=none; rua=mailto:dmarc@yourdomain.com'"
        })
    elif any('p=none' in r['record'] for r in dmarc_result['records']):
        results["recommendations"].append({
            "type": "info",
            "title": "Strengthen DMARC Policy",
            "description": "Consider changing 'p=none' to 'p=quarantine' or 'p=reject' for better protection."
        })
    
    if not dkim_result['has_dkim']:
        results["recommendations"].append({
            "type": "info",
            "title": "Consider DKIM",
            "description": "DKIM provides email authentication. This is typically configured by your email service provider."
        })
    elif len(dkim_result['records']) == 1:
        # Only recommend multiple DKIM selectors for non-Google providers
        if email_provider != "Google Workspace":
            results["recommendations"].append({
                "type": "info",
                "title": "Consider Multiple DKIM Selectors",
                "description": "Multiple DKIM selectors provide better authentication diversity and security."
            })
        else:
            results["recommendations"].append({
                "type": "info",
                "title": "DKIM Configuration Complete",
                "description": "Google Workspace uses a single DKIM selector which is the standard configuration."
            })
    
    # Store analysis results in Firestore
    try:
        firestore_manager.store_analysis(domain, results)
        logger.info(f"Analysis stored in Firestore for {domain}")
    except Exception as e:
        logger.warning(f"Failed to store analysis in Firestore: {e}")
    
    logger.info(f"Analysis completed for {domain}. Security score: {security_score['score']}, Provider: {email_provider}")
    return jsonify(results)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "astraverify-backend", "version": "progressive-fix"})

@app.route('/api/dkim/check-selector', methods=['GET'])
def check_dkim_selector():
    """Check if a specific DKIM selector exists for a domain"""
    domain = request.args.get('domain')
    selector = request.args.get('selector')
    
    if not domain or not selector:
        return jsonify({"error": "Both domain and selector parameters are required"}), 400
    
    try:
        dkim_domain = f"{selector}._domainkey.{domain}"
        records = dns.resolver.resolve(dkim_domain, 'TXT')
        
        dkim_records = []
        for record in records:
            record_text = record.to_text().strip('"')
            if record_text.startswith('v=DKIM1'):
                dkim_records.append({
                    'selector': selector,
                    'record': record_text[:100] + '...' if len(record_text) > 100 else record_text,
                    'valid': True,
                    'full_record': record_text
                })
        
        if dkim_records:
            return jsonify({
                "found": True,
                "selector": selector,
                "domain": domain,
                "records": dkim_records,
                "message": f"DKIM record found for selector '{selector}'"
            })
        else:
            return jsonify({
                "found": False,
                "selector": selector,
                "domain": domain,
                "message": f"No DKIM record found for selector '{selector}'"
            })
    except dns.resolver.NXDOMAIN:
        return jsonify({
            "found": False,
            "selector": selector,
            "domain": domain,
            "message": f"No DKIM record found for selector '{selector}'"
        })
    except Exception as e:
        return jsonify({
            "found": False,
            "selector": selector,
            "domain": domain,
            "error": str(e),
            "message": f"Error checking DKIM selector '{selector}'"
        }), 500

@app.route('/api/dkim/suggest-selectors', methods=['GET'])
def suggest_dkim_selectors():
    """Suggest DKIM selectors based on email provider patterns"""
    domain = request.args.get('domain')
    
    if not domain:
        return jsonify({"error": "Domain parameter is required"}), 400
    
    # Get MX records to suggest selectors based on email provider
    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        mx_servers = [str(mx.exchange).lower() for mx in mx_records]
        
        suggestions = []
        
        # Suggest based on MX server patterns
        if any('google' in server for server in mx_servers):
            suggestions.extend(['google', 'google1', 'google2', 'google2025'])
        elif any('outlook' in server or 'microsoft' in server for server in mx_servers):
            suggestions.extend(['selector1', 'selector2', 's1', 's2'])
        elif any('yahoo' in server for server in mx_servers):
            suggestions.extend(['yahoo', 'ya'])
        elif any('zoho' in server for server in mx_servers):
            suggestions.extend(['zoho', 'zohomail'])
        elif any('mailgun' in server for server in mx_servers):
            suggestions.extend(['mailgun', 'mg'])
        elif any('sendgrid' in server for server in mx_servers):
            suggestions.extend(['sendgrid', 'sg'])
        elif any('dreamhost' in server for server in mx_servers):
            suggestions.extend(['dreamhost'])
        
        # Add common selectors
        suggestions.extend(['default', 'k1', 'selector1', 'selector2'])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_suggestions = []
        for s in suggestions:
            if s not in seen:
                unique_suggestions.append(s)
                seen.add(s)
        
        return jsonify({
            "domain": domain,
            "suggestions": unique_suggestions[:10],  # Limit to top 10
            "message": f"Suggested DKIM selectors for {domain}"
        })
        
    except Exception as e:
        return jsonify({
            "domain": domain,
            "suggestions": ['default', 'google', 'selector1', 'selector2', 'k1'],
            "message": f"Using default suggestions (error: {str(e)})"
        })

@app.route('/api/check/dkim', methods=['GET'])
def complete_dkim_check():
    """Complete DKIM check for progressive mode (optimized)"""
    domain = request.args.get('domain')
    custom_selector = request.args.get('dkim_selector')
    
    if not domain:
        return jsonify({"error": "Domain parameter is required"}), 400
    
    # Remove protocol if present
    domain = domain.replace('http://', '').replace('https://', '').replace('www.', '')
    
    logger.info(f"Completing optimized DKIM analysis for domain: {domain}")
    
    # Get MX servers for provider-specific selector prioritization
    mx_servers = []
    try:
        mx_result = get_mx_details(domain)
        if mx_result.get('has_mx'):
            mx_servers = [record['server'] for record in mx_result.get('records', [])]
    except:
        pass
    
    # Get optimized DKIM results
    dkim_result = dkim_optimizer_sync.get_dkim_details_optimized(domain, custom_selector, mx_servers)
    
    # Detect email provider based on DKIM
    spf_result = get_spf_details(domain)
    email_provider = detect_email_provider(mx_result, spf_result, dkim_result)
    
    # Calculate security score
    dmarc_result = get_dmarc_details(domain)
    security_score = get_security_score(mx_result, spf_result, dmarc_result, dkim_result)
    
    # Generate recommendations
    recommendations = []
    
    try:
        # Generate enhanced recommendations based on email provider
        if not mx_result['has_mx']:
            recommendations.append({
                "type": "critical",
                "title": "Add MX Records",
                "description": "MX records are essential for email delivery. Contact your DNS provider to add MX records."
            })
        elif len(mx_result['records']) == 1:
            recommendations.append({
                "type": "info",
                "title": "Consider Multiple MX Records",
                "description": "Adding secondary MX records improves email delivery reliability and redundancy."
            })
        
        if not spf_result['has_spf']:
            if email_provider == "Google Workspace":
                recommendations.append({
                    "type": "important",
                    "title": "Add SPF Record",
                    "description": "SPF records help prevent email spoofing. Add a TXT record with 'v=spf1 include:_spf.google.com ~all' for Google Workspace."
                })
            elif email_provider == "Microsoft 365":
                recommendations.append({
                    "type": "important",
                    "title": "Add SPF Record",
                    "description": "SPF records help prevent email spoofing. Add a TXT record with 'v=spf1 include:spf.protection.outlook.com ~all' for Microsoft 365."
                })
            else:
                recommendations.append({
                    "type": "important",
                    "title": "Add SPF Record",
                    "description": "SPF records help prevent email spoofing. Contact your email service provider for the correct SPF record."
                })
        elif any('~all' in r['record'] for r in spf_result['records']):
            recommendations.append({
                "type": "info",
                "title": "Strengthen SPF Policy",
                "description": "Consider changing '~all' to '-all' for stronger spoofing protection."
            })
        
        if not dmarc_result['has_dmarc']:
            recommendations.append({
                "type": "important",
                "title": "Add DMARC Record",
                "description": "DMARC records provide email authentication reporting. Add a TXT record at _dmarc.yourdomain.com with 'v=DMARC1; p=none; rua=mailto:dmarc@yourdomain.com'"
            })
        elif any('p=none' in r['record'] for r in dmarc_result['records']):
            recommendations.append({
                "type": "info",
                "title": "Strengthen DMARC Policy",
                "description": "Consider changing 'p=none' to 'p=quarantine' or 'p=reject' for better protection."
            })
        
        if not dkim_result['has_dkim']:
            recommendations.append({
                "type": "info",
                "title": "Consider DKIM",
                "description": "DKIM provides email authentication. This is typically configured by your email service provider."
            })
        elif len(dkim_result['records']) == 1:
            # Only recommend multiple DKIM selectors for non-Google providers
            if email_provider != "Google Workspace":
                recommendations.append({
                    "type": "info",
                    "title": "Consider Multiple DKIM Selectors",
                    "description": "Multiple DKIM selectors provide better authentication diversity and security."
                })
            else:
                recommendations.append({
                    "type": "info",
                    "title": "DKIM Configuration Complete",
                    "description": "Google Workspace uses a single DKIM selector which is the standard configuration."
                })
    except Exception as e:
        recommendations = []
    
    # Remove internal timing info
    dkim_response = {
        "enabled": dkim_result['has_dkim'],
        "status": dkim_result['status'],
        "description": dkim_result['description'],
        "records": dkim_result['records'],
        "selectors_checked": dkim_result.get('selectors_checked', 0)
    }
    
    # Add performance info in development
    if ENVIRONMENT == 'development' and 'check_time' in dkim_result:
        dkim_response['check_time'] = dkim_result['check_time']
    
    return jsonify({
        "domain": domain,
        "dkim": dkim_response,
        "email_provider": email_provider,
        "security_score": security_score,
        "recommendations": recommendations,
        "completed": True
    })

@app.route('/api/analytics/recent', methods=['GET'])
@require_admin_auth
def get_recent_analyses():
    """Get recent domain analyses"""
    try:
        limit = int(request.args.get('limit', 10))
        analyses = firestore_manager.get_recent_analyses(limit)
        return jsonify({
            "success": True,
            "data": analyses,
            "count": len(analyses)
        })
    except Exception as e:
        logger.error(f"Failed to get recent analyses: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/analytics/history/<domain>', methods=['GET'])
@require_admin_auth
def get_domain_history(domain):
    """Get analysis history for a specific domain"""
    try:
        limit = int(request.args.get('limit', 20))
        history = firestore_manager.get_domain_history(domain, limit)
        return jsonify({
            "success": True,
            "domain": domain,
            "data": history,
            "count": len(history)
        })
    except Exception as e:
        logger.error(f"Failed to get history for {domain}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/analytics/statistics', methods=['GET'])
@require_admin_auth
def get_analytics_statistics():
    """Get analytics statistics"""
    try:
        stats = firestore_manager.get_statistics()
        return jsonify({
            "success": True,
            "data": stats
        })
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/public/statistics', methods=['GET'])
def get_public_statistics():
    """Get public statistics (no admin required)"""
    try:
        stats = firestore_manager.get_statistics()
        # Return only basic stats for public consumption
        public_stats = {
            "total_analyses": stats.get('total_analyses', 0),
            "unique_domains": stats.get('unique_domains', 0),
            "average_security_score": stats.get('average_security_score', 0),
            "email_provider_distribution": stats.get('email_provider_distribution', {})
        }
        return jsonify({
            "success": True,
            "data": public_stats
        })
    except Exception as e:
        logger.error(f"Failed to get public statistics: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/test-email', methods=['GET'])
def test_email_config():
    """Test email configuration"""
    try:
        if not EMAIL_PASSWORD:
            return jsonify({
                "success": False,
                "error": "Email password not configured"
            }), 400
        
        # Test SMTP connection
        server = smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT)
        server.starttls()
        
        # Try different authentication methods
        try:
            server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            logger.info("Test: SMTP authentication successful with LOGIN")
        except Exception as login_error:
            logger.warning(f"Test: LOGIN authentication failed: {login_error}")
            # Try PLAIN authentication as fallback
            try:
                server.ehlo()
                server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
                logger.info("Test: SMTP authentication successful with PLAIN")
            except Exception as plain_error:
                logger.error(f"Test: PLAIN authentication also failed: {plain_error}")
                raise plain_error
        
        server.quit()
        
        return jsonify({
            "success": True,
            "message": "Email configuration is working",
            "config": {
                "smtp_server": EMAIL_SMTP_SERVER,
                "smtp_port": EMAIL_SMTP_PORT,
                "username": EMAIL_USERNAME,
                "sender": EMAIL_SENDER,
                "password_configured": bool(EMAIL_PASSWORD)
            }
        })
        
    except Exception as e:
        logger.error(f"Email configuration test failed: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "config": {
                "smtp_server": EMAIL_SMTP_SERVER,
                "smtp_port": EMAIL_SMTP_PORT,
                "username": EMAIL_USERNAME,
                "sender": EMAIL_SENDER,
                "password_configured": bool(EMAIL_PASSWORD)
            }
        }), 500

@app.route('/api/email-report', methods=['POST'])
def send_email_report_endpoint():
    """Send email report with analysis results"""
    try:
        data = request.get_json()
        email = data.get('email')
        domain = data.get('domain')
        analysis_result = data.get('analysis_result')
        opt_in_marketing = data.get('opt_in_marketing', False)
        timestamp = data.get('timestamp')
        
        if not email or not domain or not analysis_result:
            return jsonify({"success": False, "error": "Missing required fields"}), 400
        
        # Send actual email
        if EMAIL_PASSWORD:
            email_sent = send_email_report(email, domain, analysis_result, opt_in_marketing)
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
        logger.error(f"Failed to process email report: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        "message": "AstraVerify Backend API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/health",
            "check_domain": "/api/check?domain=example.com",
            "public": {
                "statistics": "/api/public/statistics"
            },
            "admin": {
                "recent": "/api/analytics/recent?limit=10",
                "history": "/api/analytics/history/{domain}?limit=20",
                "statistics": "/api/analytics/statistics"
            }
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
