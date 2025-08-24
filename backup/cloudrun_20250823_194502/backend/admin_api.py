import os
import logging
import re
import jwt
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from flask import Flask, request, jsonify, g, redirect, url_for, session
from functools import wraps
from dotenv import load_dotenv
from dkim_selector_manager import dkim_selector_manager
from enhanced_dkim_scanner import enhanced_dkim_scanner
from ip_blocker import IPBlocker

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Google OAuth Configuration
GOOGLE_OAUTH_CONFIG = {
    'client_id': os.environ.get('GOOGLE_OAUTH_CLIENT_ID', 'your-google-oauth-client-id.apps.googleusercontent.com'),
    'client_secret': os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET', 'your-google-oauth-client-secret'),
    'redirect_uri': os.environ.get('GOOGLE_OAUTH_REDIRECT_URI', 'http://localhost:5001/admin/auth/callback'),
    'scopes': [
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile'
    ],
    'authorized_domains': ['astraverify.com', 'cloudgofer.com']
}

# JWT Configuration
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 8

class AdminAuthorization:
    """Admin authorization and authentication management"""
    
    def __init__(self):
        self.authorized_domains = GOOGLE_OAUTH_CONFIG['authorized_domains']
        self.admin_roles = {
            'super_admin': ['hi@astraverify.com', 'admin@astraverify.com'],
            'domain_admin': ['*@astraverify.com'],  # All astraverify.com users
            'limited_admin': ['support@astraverify.com']
        }
    
    def is_authorized(self, email: str) -> Tuple[bool, str]:
        """Check if user is authorized for admin access"""
        domain = email.split('@')[1]
        
        # Check domain authorization
        if domain not in self.authorized_domains:
            return False, "Unauthorized domain"
        
        # Check role-based authorization
        for role, authorized_emails in self.admin_roles.items():
            if email in authorized_emails:
                return True, role
            elif '*@' + domain in authorized_emails:
                return True, role
        
        return False, "Insufficient permissions"
    
    def get_user_permissions(self, email: str) -> Dict[str, bool]:
        """Get specific permissions for user"""
        is_auth, role = self.is_authorized(email)
        
        if not is_auth:
            return {}
        
        permissions = {
            'super_admin': {
                'can_manage_users': True,
                'can_manage_domains': True,
                'can_manage_selectors': True,
                'can_view_analytics': True,
                'can_manage_system': True,
                'can_manage_brute_force': True,
                'can_manage_ip_blocks': True
            },
            'domain_admin': {
                'can_manage_users': False,
                'can_manage_domains': True,
                'can_manage_selectors': True,
                'can_view_analytics': True,
                'can_manage_system': False,
                'can_manage_brute_force': True,
                'can_manage_ip_blocks': True
            },
            'limited_admin': {
                'can_manage_users': False,
                'can_manage_domains': False,
                'can_manage_selectors': True,
                'can_view_analytics': False,
                'can_manage_system': False,
                'can_manage_brute_force': False,
                'can_manage_ip_blocks': False
            }
        }
        
        return permissions.get(role, {})

class AdminSessionManager:
    """Admin session management with JWT"""
    
    def __init__(self):
        self.secret_key = JWT_SECRET_KEY
        self.algorithm = JWT_ALGORITHM
        self.expiration_hours = JWT_EXPIRATION_HOURS
    
    def create_session(self, user_info: Dict[str, Any]) -> str:
        """Create JWT session token for admin user"""
        payload = {
            'email': user_info['email'],
            'name': user_info.get('name', ''),
            'picture': user_info.get('picture', ''),
            'role': user_info.get('role', 'domain_admin'),
            'permissions': user_info.get('permissions', {}),
            'exp': datetime.utcnow() + timedelta(hours=self.expiration_hours),
            'iat': datetime.utcnow()
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def validate_session(self, token: str) -> Tuple[bool, Dict[str, Any]]:
        """Validate JWT session token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return True, payload
        except jwt.ExpiredSignatureError:
            return False, {"error": "Session expired"}
        except jwt.InvalidTokenError:
            return False, {"error": "Invalid token"}

# Initialize admin components
admin_auth = AdminAuthorization()
session_manager = AdminSessionManager()
ip_blocker = IPBlocker()

def require_admin_auth(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check environment for local development bypass
        environment = os.environ.get('ENVIRONMENT', 'local')
        
        if environment == 'local':
            # Local development - bypass authentication
            g.admin_user = {
                'email': 'admin@astraverify.com',
                'name': 'Local Admin User',
                'role': 'super_admin',
                'permissions': {
                    'can_manage_users': True,
                    'can_manage_domains': True,
                    'can_manage_selectors': True,
                    'can_view_analytics': True,
                    'can_manage_system': True,
                    'can_manage_brute_force': True,
                    'can_manage_ip_blocks': True
                }
            }
            return f(*args, **kwargs)
        
        # Production/Staging - require authentication
        # Check for token in Authorization header first, then cookies
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        else:
            token = request.cookies.get('admin_token')
        
        if not token:
            return jsonify({"error": "Authentication required"}), 401
        
        is_valid, payload = session_manager.validate_session(token)
        
        if not is_valid:
            return jsonify({"error": "Invalid or expired session"}), 401
        
        # Add user info to request context
        g.admin_user = payload
        
        return f(*args, **kwargs)
    
    return decorated_function

def require_permission(permission: str):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check environment for local development bypass
            environment = os.environ.get('ENVIRONMENT', 'local')
            
            if environment == 'local':
                # Local development - bypass permission checks
                return f(*args, **kwargs)
            
            # Production/Staging - check permissions
            if not hasattr(g, 'admin_user'):
                return jsonify({"error": "Authentication required"}), 401
            
            user_permissions = g.admin_user.get('permissions', {})
            if not user_permissions.get(permission, False):
                return jsonify({"error": "Insufficient permissions"}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Admin API Routes
def create_admin_routes(app):
    """Create admin API routes"""
    
    @app.route('/admin')
    def admin_home():
        """Admin home page - redirects to login if not authenticated"""
        token = request.cookies.get('admin_token')
        
        if token:
            is_valid, payload = session_manager.validate_session(token)
            if is_valid:
                return jsonify({
                    "authenticated": True,
                    "user": {
                        "email": payload['email'],
                        "name": payload['name'],
                        "role": payload['role'],
                        "permissions": payload['permissions']
                    }
                })
        
        return jsonify({"authenticated": False, "login_url": "/admin/auth/google"})
    
    @app.route('/admin/auth/google')
    def admin_google_auth():
        """Initiate Google OAuth flow"""
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?" + \
                   f"client_id={GOOGLE_OAUTH_CONFIG['client_id']}&" + \
                   f"redirect_uri={GOOGLE_OAUTH_CONFIG['redirect_uri']}&" + \
                   f"scope={' '.join(GOOGLE_OAUTH_CONFIG['scopes'])}&" + \
                   f"response_type=code&" + \
                   f"access_type=offline"
        
        return jsonify({"auth_url": auth_url})
    
    @app.route('/admin/auth/callback')
    def admin_auth_callback():
        """Handle Google OAuth callback"""
        code = request.args.get('code')
        
        if not code:
            return jsonify({"error": "No authorization code provided"}), 400
        
        try:
            # Exchange code for tokens
            token_response = requests.post('https://oauth2.googleapis.com/token', data={
                'client_id': GOOGLE_OAUTH_CONFIG['client_id'],
                'client_secret': GOOGLE_OAUTH_CONFIG['client_secret'],
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': GOOGLE_OAUTH_CONFIG['redirect_uri']
            })
            
            if token_response.status_code != 200:
                return jsonify({"error": "Failed to exchange authorization code"}), 400
            
            tokens = token_response.json()
            
            # Get user info
            user_response = requests.get('https://www.googleapis.com/oauth2/v2/userinfo', headers={
                'Authorization': f"Bearer {tokens['access_token']}"
            })
            
            if user_response.status_code != 200:
                return jsonify({"error": "Failed to get user info"}), 400
            
            user_info = user_response.json()
            
            # Check authorization
            is_authorized, role = admin_auth.is_authorized(user_info['email'])
            
            if not is_authorized:
                return jsonify({"error": "Unauthorized domain or insufficient permissions"}), 403
            
            # Create session
            user_info['role'] = role
            user_info['permissions'] = admin_auth.get_user_permissions(user_info['email'])
            
            session_token = session_manager.create_session(user_info)
            
            response = jsonify({
                "success": True,
                "message": "Authentication successful",
                "user": {
                    "email": user_info['email'],
                    "name": user_info['name'],
                    "role": role,
                    "permissions": user_info['permissions']
                },
                "token": session_token
            })
            
            # Set the token as a cookie for server-side access
            response.set_cookie('admin_token', session_token, max_age=8*60*60, httponly=False, samesite='Lax')
            
            # Redirect to login page with success and token
            return redirect(f'/admin/ui/login?auth_result=success&token={session_token}')
            
        except Exception as e:
            logger.error(f"Admin auth error: {e}")
            return jsonify({"error": "Authentication failed"}), 500
    
    @app.route('/admin/logout')
    def admin_logout():
        """Admin logout"""
        return jsonify({"success": True, "message": "Logged out successfully"})
    
    # DKIM Selector Management Routes
    
    @app.route('/admin/domains/<domain>/selectors', methods=['GET'])
    @require_admin_auth
    @require_permission('can_manage_selectors')
    def get_domain_selectors(domain):
        """Get all DKIM selectors for a domain"""
        try:
            summary = dkim_selector_manager.get_domain_selector_summary(domain)
            return jsonify(summary)
        except Exception as e:
            logger.error(f"Failed to get selectors for {domain}: {e}")
            return jsonify({"error": "Failed to get selectors"}), 500
    
    @app.route('/admin/domains/<domain>/selectors', methods=['POST'])
    @require_admin_auth
    @require_permission('can_manage_selectors')
    def add_dkim_selector(domain):
        """Add a new DKIM selector for a domain"""
        try:
            data = request.get_json()
            selector = data.get('selector')
            notes = data.get('notes', '')
            priority = data.get('priority', 'medium')
            
            if not selector:
                return jsonify({"error": "Selector is required"}), 400
            
            # Validate selector format
            if not re.match(r'^[a-zA-Z0-9_-]+$', selector):
                return jsonify({"error": "Invalid selector format"}), 400
            
            # Add selector
            success = dkim_selector_manager.add_admin_selector(
                domain=domain,
                selector=selector,
                notes=notes,
                priority=priority,
                added_by=g.admin_user['email']
            )
            
            if success:
                return jsonify({
                    "success": True,
                    "message": f"Selector '{selector}' added successfully"
                })
            else:
                return jsonify({"error": "Failed to add selector"}), 500
                
        except Exception as e:
            logger.error(f"Failed to add selector for {domain}: {e}")
            return jsonify({"error": "Failed to add selector"}), 500
    
    @app.route('/admin/domains/<domain>/selectors/<selector>', methods=['DELETE'])
    @require_admin_auth
    @require_permission('can_manage_selectors')
    def remove_dkim_selector(domain, selector):
        """Remove a DKIM selector from a domain"""
        try:
            success = dkim_selector_manager.remove_admin_selector(domain, selector)
            
            if success:
                return jsonify({
                    "success": True,
                    "message": f"Selector '{selector}' removed successfully"
                })
            else:
                return jsonify({"error": "Failed to remove selector"}), 500
                
        except Exception as e:
            logger.error(f"Failed to remove selector {selector} for {domain}: {e}")
            return jsonify({"error": "Failed to remove selector"}), 500
    
    @app.route('/admin/domains/<domain>/selectors/<selector>/test', methods=['GET'])
    @require_admin_auth
    @require_permission('can_manage_selectors')
    def test_dkim_selector(domain, selector):
        """Test a specific DKIM selector"""
        try:
            test_result = dkim_selector_manager._test_selector(domain, selector)
            return jsonify({
                "domain": domain,
                "selector": selector,
                "test_result": test_result
            })
        except Exception as e:
            logger.error(f"Failed to test selector {selector} for {domain}: {e}")
            return jsonify({"error": "Failed to test selector"}), 500
    
    @app.route('/admin/domains/<domain>/scan', methods=['POST'])
    @require_admin_auth
    @require_permission('can_manage_selectors')
    def scan_domain_dkim(domain):
        """Perform comprehensive DKIM scan for a domain"""
        try:
            data = request.get_json() or {}
            custom_selector = data.get('custom_selector')
            
            # Perform scan
            scan_result = enhanced_dkim_scanner.scan_domain_dkim(domain, custom_selector)
            
            return jsonify({
                "success": True,
                "scan_result": scan_result
            })
            
        except Exception as e:
            logger.error(f"Failed to scan domain {domain}: {e}")
            return jsonify({"error": "Failed to scan domain"}), 500
    
    # Brute Force Selector Management
    
    @app.route('/admin/brute-force-selectors', methods=['GET'])
    @require_admin_auth
    @require_permission('can_manage_brute_force')
    def get_brute_force_selectors():
        """Get current brute force selectors"""
        try:
            selectors = dkim_selector_manager.get_brute_force_selectors()
            return jsonify({
                "selectors": selectors,
                "total": len(selectors)
            })
        except Exception as e:
            logger.error(f"Failed to get brute force selectors: {e}")
            return jsonify({"error": "Failed to get selectors"}), 500
    
    @app.route('/admin/brute-force-selectors', methods=['PUT'])
    @require_admin_auth
    @require_permission('can_manage_brute_force')
    def update_brute_force_selectors():
        """Update brute force selectors"""
        try:
            data = request.get_json()
            selectors = data.get('selectors', [])
            
            if not isinstance(selectors, list):
                return jsonify({"error": "Selectors must be a list"}), 400
            
            # Validate selectors
            for selector in selectors:
                if not re.match(r'^[a-zA-Z0-9_-]+$', selector):
                    return jsonify({"error": f"Invalid selector format: {selector}"}), 400
            
            success = dkim_selector_manager.update_brute_force_selectors(selectors)
            
            if success:
                return jsonify({
                    "success": True,
                    "message": f"Updated {len(selectors)} brute force selectors"
                })
            else:
                return jsonify({"error": "Failed to update selectors"}), 500
                
        except Exception as e:
            logger.error(f"Failed to update brute force selectors: {e}")
            return jsonify({"error": "Failed to update selectors"}), 500
    
    # Analytics and Statistics
    
    @app.route('/admin/analytics/selectors', methods=['GET'])
    @require_admin_auth
    @require_permission('can_view_analytics')
    def get_selector_analytics():
        """Get selector analytics and statistics"""
        try:
            # This would be implemented to provide comprehensive analytics
            # For now, return basic structure
            return jsonify({
                "total_domains_with_selectors": 0,
                "total_admin_selectors": 0,
                "total_discovered_selectors": 0,
                "most_common_selectors": [],
                "success_rate_by_source": {
                    "admin": 0.0,
                    "discovered": 0.0,
                    "brute_force": 0.0
                }
            })
        except Exception as e:
            logger.error(f"Failed to get selector analytics: {e}")
            return jsonify({"error": "Failed to get analytics"}), 500
    
    # IP Management Routes
    
    @app.route('/admin/ip-blocks', methods=['GET'])
    @require_admin_auth
    @require_permission('can_manage_ip_blocks')
    def get_blocked_ips():
        """Get all currently blocked IP addresses"""
        try:
            blocked_ips = ip_blocker.get_blocked_ips()
            return jsonify({
                "blocked_ips": blocked_ips,
                "total_blocked": len(blocked_ips)
            })
        except Exception as e:
            logger.error(f"Failed to get blocked IPs: {e}")
            return jsonify({"error": "Failed to get blocked IPs"}), 500
    
    @app.route('/admin/ip-blocks/<ip>', methods=['GET'])
    @require_admin_auth
    @require_permission('can_manage_ip_blocks')
    def get_ip_block_info(ip):
        """Get detailed information about a blocked IP"""
        try:
            block_info = ip_blocker.get_block_info(ip)
            if block_info:
                return jsonify({
                    "ip": ip,
                    "block_info": block_info
                })
            else:
                return jsonify({"error": "IP not found in blocked list"}), 404
        except Exception as e:
            logger.error(f"Failed to get block info for IP {ip}: {e}")
            return jsonify({"error": "Failed to get block info"}), 500
    
    @app.route('/admin/ip-blocks/<ip>', methods=['DELETE'])
    @require_admin_auth
    @require_permission('can_manage_ip_blocks')
    def unblock_ip(ip):
        """Unblock an IP address (temporary or permanent)"""
        try:
            success = ip_blocker.unblock_ip(ip)
            if success:
                return jsonify({
                    "success": True,
                    "message": f"IP {ip} unblocked successfully"
                })
            else:
                return jsonify({"error": "IP not found in blocked list"}), 404
        except Exception as e:
            logger.error(f"Failed to unblock IP {ip}: {e}")
            return jsonify({"error": "Failed to unblock IP"}), 500
    
    @app.route('/admin/ip-blocks/<ip>', methods=['POST'])
    @require_admin_auth
    @require_permission('can_manage_ip_blocks')
    def block_ip(ip):
        """Block an IP address with specified level and reason"""
        try:
            data = request.get_json()
            reason = data.get('reason', 'Manual block by admin')
            level = data.get('level', 'temporary')
            
            if level not in ['temporary', 'extended', 'permanent']:
                return jsonify({"error": "Invalid block level. Must be temporary, extended, or permanent"}), 400
            
            success = ip_blocker.block_ip(ip, reason, level)
            if success:
                return jsonify({
                    "success": True,
                    "message": f"IP {ip} blocked successfully with level {level}"
                })
            else:
                return jsonify({"error": "Failed to block IP"}), 500
        except Exception as e:
            logger.error(f"Failed to block IP {ip}: {e}")
            return jsonify({"error": "Failed to block IP"}), 500
    
    @app.route('/admin/ip-blocks/<ip>/extend', methods=['POST'])
    @require_admin_auth
    @require_permission('can_manage_ip_blocks')
    def extend_ip_block(ip):
        """Extend the block duration for an IP"""
        try:
            data = request.get_json()
            additional_hours = data.get('additional_hours', 6)
            
            if not isinstance(additional_hours, (int, float)) or additional_hours <= 0:
                return jsonify({"error": "Additional hours must be a positive number"}), 400
            
            from datetime import timedelta
            additional_time = timedelta(hours=additional_hours)
            
            success = ip_blocker.extend_block(ip, additional_time)
            if success:
                return jsonify({
                    "success": True,
                    "message": f"IP {ip} block extended by {additional_hours} hours"
                })
            else:
                return jsonify({"error": "IP not found in blocked list or cannot extend"}), 404
        except Exception as e:
            logger.error(f"Failed to extend block for IP {ip}: {e}")
            return jsonify({"error": "Failed to extend block"}), 500
    
    @app.route('/admin/ip-blocks/<ip>/reason', methods=['PUT'])
    @require_admin_auth
    @require_permission('can_manage_ip_blocks')
    def update_block_reason(ip):
        """Update the reason for blocking an IP"""
        try:
            data = request.get_json()
            new_reason = data.get('reason')
            
            if not new_reason:
                return jsonify({"error": "Reason is required"}), 400
            
            success = ip_blocker.update_block_reason(ip, new_reason)
            if success:
                return jsonify({
                    "success": True,
                    "message": f"Updated block reason for IP {ip}"
                })
            else:
                return jsonify({"error": "IP not found in blocked list"}), 404
        except Exception as e:
            logger.error(f"Failed to update block reason for IP {ip}: {e}")
            return jsonify({"error": "Failed to update block reason"}), 500
    
    @app.route('/admin/ip-blocks/statistics', methods=['GET'])
    @require_admin_auth
    @require_permission('can_manage_ip_blocks')
    def get_ip_block_statistics():
        """Get statistics about blocked IPs"""
        try:
            stats = ip_blocker.get_block_statistics()
            return jsonify(stats)
        except Exception as e:
            logger.error(f"Failed to get IP block statistics: {e}")
            return jsonify({"error": "Failed to get statistics"}), 500
    
    # Premium IP Management Routes
    
    @app.route('/admin/premium-ips', methods=['GET'])
    @require_admin_auth
    @require_permission('can_manage_ip_blocks')
    def get_premium_ips():
        """Get all premium IP addresses"""
        try:
            # Get premium IPs from environment variable
            premium_ips_str = os.environ.get('PREMIUM_IPS', '')
            premium_ips = [ip.strip() for ip in premium_ips_str.split(',') if ip.strip()]
            
            return jsonify({
                "premium_ips": premium_ips,
                "total_premium": len(premium_ips)
            })
        except Exception as e:
            logger.error(f"Failed to get premium IPs: {e}")
            return jsonify({"error": "Failed to get premium IPs"}), 500
    
    @app.route('/admin/premium-ips', methods=['POST'])
    @require_admin_auth
    @require_permission('can_manage_ip_blocks')
    def add_premium_ip():
        """Add a new premium IP address"""
        try:
            data = request.get_json()
            new_ip = data.get('ip')
            notes = data.get('notes', '')
            
            if not new_ip:
                return jsonify({"error": "IP address is required"}), 400
            
            # Validate IP format
            import re
            ip_regex = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
            if not re.match(ip_regex, new_ip):
                return jsonify({"error": "Invalid IP address format"}), 400
            
            # Get current premium IPs
            premium_ips_str = os.environ.get('PREMIUM_IPS', '')
            premium_ips = [ip.strip() for ip in premium_ips_str.split(',') if ip.strip()]
            
            # Check if IP already exists
            if new_ip in premium_ips:
                return jsonify({"error": "IP address is already in premium list"}), 400
            
            # Add new IP
            premium_ips.append(new_ip)
            new_premium_ips_str = ','.join(premium_ips)
            
            # Update environment variable (for this session)
            os.environ['PREMIUM_IPS'] = new_premium_ips_str
            
            return jsonify({
                "success": True,
                "message": f"Premium IP {new_ip} added successfully",
                "premium_ips": premium_ips,
                "total_premium": len(premium_ips)
            })
        except Exception as e:
            logger.error(f"Failed to add premium IP: {e}")
            return jsonify({"error": "Failed to add premium IP"}), 500
    
    @app.route('/admin/premium-ips/<ip>', methods=['DELETE'])
    @require_admin_auth
    @require_permission('can_manage_ip_blocks')
    def remove_premium_ip(ip):
        """Remove a premium IP address"""
        try:
            # Get current premium IPs
            premium_ips_str = os.environ.get('PREMIUM_IPS', '')
            premium_ips = [ip.strip() for ip in premium_ips_str.split(',') if ip.strip()]
            
            # Check if IP exists
            if ip not in premium_ips:
                return jsonify({"error": "IP address not found in premium list"}), 404
            
            # Remove IP
            premium_ips.remove(ip)
            new_premium_ips_str = ','.join(premium_ips)
            
            # Update environment variable (for this session)
            os.environ['PREMIUM_IPS'] = new_premium_ips_str
            
            return jsonify({
                "success": True,
                "message": f"Premium IP {ip} removed successfully",
                "premium_ips": premium_ips,
                "total_premium": len(premium_ips)
            })
        except Exception as e:
            logger.error(f"Failed to remove premium IP: {e}")
            return jsonify({"error": "Failed to remove premium IP"}), 500
    
    @app.route('/admin/premium-ips/bulk', methods=['POST'])
    @require_admin_auth
    @require_permission('can_manage_ip_blocks')
    def bulk_update_premium_ips():
        """Bulk update premium IP addresses"""
        try:
            data = request.get_json()
            premium_ips = data.get('premium_ips', [])
            
            if not isinstance(premium_ips, list):
                return jsonify({"error": "Premium IPs must be a list"}), 400
            
            # Validate all IPs
            import re
            ip_regex = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
            for ip in premium_ips:
                if not re.match(ip_regex, ip):
                    return jsonify({"error": f"Invalid IP address format: {ip}"}), 400
            
            # Update environment variable (for this session)
            new_premium_ips_str = ','.join(premium_ips)
            os.environ['PREMIUM_IPS'] = new_premium_ips_str
            
            return jsonify({
                "success": True,
                "message": f"Updated {len(premium_ips)} premium IPs",
                "premium_ips": premium_ips,
                "total_premium": len(premium_ips)
            })
        except Exception as e:
            logger.error(f"Failed to bulk update premium IPs: {e}")
            return jsonify({"error": "Failed to update premium IPs"}), 500
    
    return app
