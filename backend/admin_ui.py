from flask import Flask, render_template_string, request, jsonify, redirect, url_for
import os
import requests
from datetime import datetime

# Simple admin UI templates
ADMIN_LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AstraVerify Admin - Login</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .login-container { max-width: 400px; margin: 100px auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .login-header { text-align: center; margin-bottom: 30px; }
        .google-login-btn { width: 100%; padding: 12px; background: #4285f4; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
        .google-login-btn:hover { background: #357abd; }
        .login-info { margin-top: 20px; text-align: center; color: #666; font-size: 14px; }
        .error-message { background: #f8d7da; color: #721c24; padding: 10px; border-radius: 4px; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-header">
            <h1>🛡️ AstraVerify Admin</h1>
            <p>Domain Intelligence Platform</p>
        </div>
        
        <button class="google-login-btn" onclick="loginWithGoogle()">
            Sign in with Google
        </button>
        
        <div class="login-info">
            <p>Only authorized users from astraverify.com can access the admin panel.</p>
        </div>
        
        {% if error %}
        <div class="error-message">
            {{ error }}
        </div>
        {% endif %}
    </div>
    
    <script>
        // Check if we're returning from OAuth callback
        const urlParams = new URLSearchParams(window.location.search);
        const authResult = urlParams.get('auth_result');
        
        if (authResult === 'success') {
            // Get token from URL params or localStorage
            const token = urlParams.get('token') || localStorage.getItem('admin_token');
            if (token) {
                localStorage.setItem('admin_token', token);
                window.location.href = '/admin/ui/dashboard';
            }
        }
        
        function loginWithGoogle() {
            fetch('/admin/auth/google')
                .then(response => response.json())
                .then(data => {
                    if (data.auth_url) {
                        window.location.href = data.auth_url;
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Failed to initiate login');
                });
        }
    </script>
</body>
</html>
"""

ADMIN_DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AstraVerify Admin - Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; }
        .admin-layout { display: flex; min-height: 100vh; }
        .admin-nav { width: 250px; background: #2c3e50; color: white; padding: 20px; }
        .nav-header h2 { margin: 0 0 20px 0; }
        .user-info { margin-bottom: 30px; padding: 15px; background: rgba(255,255,255,0.1); border-radius: 4px; }
        .nav-menu { list-style: none; padding: 0; }
        .nav-menu li { margin-bottom: 10px; }
        .nav-menu a { color: white; text-decoration: none; padding: 10px; display: block; border-radius: 4px; }
        .nav-menu a:hover, .nav-menu a.active { background: rgba(255,255,255,0.1); }
        .admin-main { flex: 1; padding: 30px; }
        .dashboard-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stat-number { font-size: 24px; font-weight: bold; color: #2c3e50; }
        .logout-btn { color: #e74c3c; text-decoration: none; }
        .logout-btn:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="admin-layout">
        <nav class="admin-nav">
            <div class="nav-header">
                <h2>🛡️ AstraVerify Admin</h2>
                <div class="user-info">
                    <strong>{{ user.name }}</strong><br>
                    <small>{{ user.email }}</small><br>
                    <small>({{ user.role }})</small>
                </div>
            </div>
            
            <ul class="nav-menu">
                <li><a href="/admin/ui/dashboard" class="active">Dashboard</a></li>
                <li><a href="/admin/ui/ip-management">IP Management</a></li>
                <li><a href="/admin/domains">Domain Management</a></li>
                <li><a href="/admin/selectors">DKIM Selectors</a></li>
                <li><a href="/admin/analytics">Analytics</a></li>
            </ul>
            
            <div style="margin-top: 30px;">
                <a href="/admin/logout" class="logout-btn">Logout</a>
            </div>
        </nav>
        
        <main class="admin-main">
            <h1>Welcome, {{ user.name }}!</h1>
            
            <div class="dashboard-stats">
                <div class="stat-card">
                    <h3>Total Domains</h3>
                    <p class="stat-number">{{ stats.total_domains }}</p>
                </div>
                <div class="stat-card">
                    <h3>Active Selectors</h3>
                    <p class="stat-number">{{ stats.active_selectors }}</p>
                </div>
                <div class="stat-card">
                    <h3>Today's Scans</h3>
                    <p class="stat-number">{{ stats.today_scans }}</p>
                </div>
                <div class="stat-card">
                    <h3>Blocked IPs</h3>
                    <p class="stat-number">{{ stats.blocked_ips }}</p>
                </div>
            </div>
            
            <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h3>Quick Actions</h3>
                <p><a href="/admin/ui/ip-management">Manage IPs</a> | <a href="/admin/domains">Manage Domains</a> | <a href="/admin/selectors">Manage DKIM Selectors</a> | <a href="/admin/analytics">View Analytics</a></p>
            </div>
        </main>
    </div>
</body>
</html>
"""

DKIM_SELECTOR_MANAGEMENT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AstraVerify Admin - DKIM Selector Management</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .selector-section { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .selector-item { border: 1px solid #ddd; padding: 15px; margin-bottom: 10px; border-radius: 4px; }
        .selector-item.verified { border-left: 4px solid #28a745; }
        .selector-item.failed { border-left: 4px solid #dc3545; }
        .btn { padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; margin-right: 10px; }
        .btn-primary { background: #007bff; color: white; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-success { background: #28a745; color: white; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        .form-group input, .form-group select, .form-group textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        .modal { display: none; position: fixed; z-index: 1; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.4); }
        .modal-content { background-color: white; margin: 15% auto; padding: 20px; border-radius: 8px; width: 80%; max-width: 500px; }
        .close { color: #aaa; float: right; font-size: 28px; font-weight: bold; cursor: pointer; }
        .close:hover { color: black; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 DKIM Selector Management</h1>
            <p>Domain: <strong>{{ domain }}</strong></p>
            <button class="btn btn-primary" onclick="showAddSelectorModal()">+ Add New Selector</button>
            <button class="btn btn-success" onclick="scanDomain()">Scan Domain</button>
        </div>
        
        <div class="selector-section">
            <h3>Admin-Managed Selectors</h3>
            <div id="admin-selectors">
                {% for selector in admin_selectors %}
                <div class="selector-item {{ 'verified' if selector.verification_status == 'verified' else 'failed' }}">
                    <strong>{{ selector.selector }}</strong> ({{ selector.priority }})
                    <br><small>Added by: {{ selector.added_by }} | Status: {{ selector.verification_status }}</small>
                    <br><small>Notes: {{ selector.notes }}</small>
                    <div style="margin-top: 10px;">
                        <button class="btn btn-success" onclick="testSelector('{{ selector.selector }}')">Test</button>
                        <button class="btn btn-danger" onclick="removeSelector('{{ selector.selector }}')">Remove</button>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <div class="selector-section">
            <h3>Discovered Selectors</h3>
            <div id="discovered-selectors">
                {% for selector in discovered_selectors %}
                <div class="selector-item {{ 'verified' if selector.verification_status == 'verified' else 'failed' }}">
                    <strong>{{ selector.selector }}</strong>
                    <br><small>Source: {{ selector.source }} | Usage: {{ selector.usage_count }} times</small>
                    <br><small>Discovered: {{ selector.discovery_date }}</small>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <div class="selector-section">
            <h3>Brute Force Selectors</h3>
            <p>Total: {{ brute_force_selectors.total }} selectors</p>
            <p>Sample: {{ ', '.join(brute_force_selectors.sample) }}</p>
            <button class="btn btn-primary" onclick="showBruteForceModal()">Edit Brute Force List</button>
        </div>
    </div>
    
    <!-- Add Selector Modal -->
    <div id="addSelectorModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal('addSelectorModal')">&times;</span>
            <h3>Add DKIM Selector</h3>
            <form id="addSelectorForm">
                <div class="form-group">
                    <label>Selector Name:</label>
                    <input type="text" id="selectorName" required>
                </div>
                <div class="form-group">
                    <label>Priority:</label>
                    <select id="selectorPriority">
                        <option value="high">High</option>
                        <option value="medium" selected>Medium</option>
                        <option value="low">Low</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Notes:</label>
                    <textarea id="selectorNotes" rows="3"></textarea>
                </div>
                <button type="submit" class="btn btn-primary">Add Selector</button>
                <button type="button" class="btn btn-danger" onclick="closeModal('addSelectorModal')">Cancel</button>
            </form>
        </div>
    </div>
    
    <script>
        const domain = '{{ domain }}';
        
        // Helper function to get cookie value
        function getCookie(name) {
            const value = `; ${document.cookie}`;
            const parts = value.split(`; ${name}=`);
            if (parts.length === 2) return parts.pop().split(';').shift();
            return null;
        }
        
        // Helper function to get JWT token
        function getAuthToken() {
            return localStorage.getItem('admin_token') || getCookie('admin_token');
        }
        
        function showAddSelectorModal() {
            document.getElementById('addSelectorModal').style.display = 'block';
        }
        
        function closeModal(modalId) {
            document.getElementById(modalId).style.display = 'none';
        }
        
        document.getElementById('addSelectorForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const selector = document.getElementById('selectorName').value;
            const priority = document.getElementById('selectorPriority').value;
            const notes = document.getElementById('selectorNotes').value;
            
            // Get the JWT token from localStorage or cookies
            const token = localStorage.getItem('admin_token') || getCookie('admin_token');
            
            if (!token) {
                alert('Authentication required. Please log in again.');
                window.location.href = '/admin/ui/login';
                return;
            }
            
            fetch(`/admin/domains/${domain}/selectors`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    selector: selector,
                    priority: priority,
                    notes: notes
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Selector added successfully!');
                    location.reload();
                } else {
                    alert('Failed to add selector: ' + data.error);
                }
            })
            .catch(error => {
                alert('Error adding selector: ' + error);
            });
        });
        
        function testSelector(selector) {
            const token = getAuthToken();
            if (!token) {
                alert('Authentication required. Please log in again.');
                window.location.href = '/admin/ui/login';
                return;
            }
            
            fetch(`/admin/domains/${domain}/selectors/${selector}/test`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            })
                .then(response => response.json())
                .then(data => {
                    if (data.test_result.valid) {
                        alert(`Selector ${selector} is valid!`);
                    } else {
                        alert(`Selector ${selector} is invalid: ${data.test_result.error}`);
                    }
                })
                .catch(error => {
                    alert('Error testing selector: ' + error);
                });
        }
        
        function removeSelector(selector) {
            if (confirm(`Are you sure you want to remove selector '${selector}'?`)) {
                const token = getAuthToken();
                if (!token) {
                    alert('Authentication required. Please log in again.');
                    window.location.href = '/admin/ui/login';
                    return;
                }
                
                fetch(`/admin/domains/${domain}/selectors/${selector}`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Selector removed successfully!');
                        location.reload();
                    } else {
                        alert('Failed to remove selector: ' + data.error);
                    }
                })
                .catch(error => {
                    alert('Error removing selector: ' + error);
                });
            }
        }
        
        function scanDomain() {
            fetch(`/admin/domains/${domain}/scan`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Domain scan completed! Check the results.');
                    location.reload();
                } else {
                    alert('Failed to scan domain: ' + data.error);
                }
            })
            .catch(error => {
                alert('Error scanning domain: ' + error);
            });
        }
    </script>
</body>
</html>
"""

IP_MANAGEMENT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AstraVerify Admin - IP Management</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; }
        .admin-layout { display: flex; min-height: 100vh; }
        .admin-nav { width: 250px; background: #2c3e50; color: white; padding: 20px; }
        .nav-header h2 { margin: 0 0 20px 0; }
        .user-info { margin-bottom: 30px; padding: 15px; background: rgba(255,255,255,0.1); border-radius: 4px; }
        .nav-menu { list-style: none; padding: 0; }
        .nav-menu li { margin-bottom: 10px; }
        .nav-menu a { color: white; text-decoration: none; padding: 10px; display: block; border-radius: 4px; }
        .nav-menu a:hover, .nav-menu a.active { background: rgba(255,255,255,0.1); }
        .admin-main { flex: 1; padding: 30px; }
        .ip-section { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .ip-item { border: 1px solid #ddd; padding: 15px; margin-bottom: 10px; border-radius: 4px; display: flex; justify-content: space-between; align-items: center; }
        .ip-item.blocked { border-left: 4px solid #dc3545; background: #fff5f5; }
        .ip-item.premium { border-left: 4px solid #28a745; background: #f0fff4; }
        .ip-item.temporary { border-left: 4px solid #ffc107; background: #fffbf0; }
        .ip-item.permanent { border-left: 4px solid #dc3545; background: #fff5f5; }
        .ip-info { flex: 1; }
        .ip-actions { display: flex; gap: 10px; }
        .btn { padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
        .btn-primary { background: #007bff; color: white; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-success { background: #28a745; color: white; }
        .btn-warning { background: #ffc107; color: black; }
        .btn-info { background: #17a2b8; color: white; }
        .status-badge { padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }
        .status-blocked { background: #dc3545; color: white; }
        .status-premium { background: #28a745; color: white; }
        .status-normal { background: #6c757d; color: white; }
        .status-temporary { background: #ffc107; color: black; }
        .status-permanent { background: #dc3545; color: white; }
        .refresh-btn { background: #17a2b8; color: white; padding: 10px 20px; margin-bottom: 20px; }
        .loading { opacity: 0.5; pointer-events: none; }
        .error-message { background: #f8d7da; color: #721c24; padding: 10px; border-radius: 4px; margin-bottom: 20px; }
        .success-message { background: #d4edda; color: #155724; padding: 10px; border-radius: 4px; margin-bottom: 20px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }
        .stat-number { font-size: 24px; font-weight: bold; color: #2c3e50; }
        .modal { display: none; position: fixed; z-index: 1; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.4); }
        .modal-content { background-color: white; margin: 15% auto; padding: 20px; border-radius: 8px; width: 80%; max-width: 500px; }
        .close { color: #aaa; float: right; font-size: 28px; font-weight: bold; cursor: pointer; }
        .close:hover { color: black; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        .form-group input, .form-group select, .form-group textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        .ip-analytics { background: #f8f9fa; padding: 10px; border-radius: 4px; margin-top: 10px; font-size: 12px; }
    </style>
</head>
<body>
    <div class="admin-layout">
        <nav class="admin-nav">
            <div class="nav-header">
                <h2>🛡️ AstraVerify Admin</h2>
                <div class="user-info">
                    <strong>{{ user.name }}</strong><br>
                    <small>{{ user.email }}</small><br>
                    <small>({{ user.role }})</small>
                </div>
            </div>
            
            <ul class="nav-menu">
                <li><a href="/admin/ui/dashboard">Dashboard</a></li>
                <li><a href="/admin/ui/ip-management" class="active">IP Management</a></li>
                <li><a href="/admin/domains">Domain Management</a></li>
                <li><a href="/admin/selectors">DKIM Selectors</a></li>
                <li><a href="/admin/analytics">Analytics</a></li>
            </ul>
            
            <div style="margin-top: 30px;">
                <a href="/admin/logout" class="logout-btn">Logout</a>
            </div>
        </nav>
        
        <main class="admin-main">
            <h1>🔒 IP Management Dashboard</h1>
            
            <div id="messages"></div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>Total Blocked</h3>
                    <p class="stat-number" id="total-blocked">-</p>
                </div>
                <div class="stat-card">
                    <h3>Temporary Blocks</h3>
                    <p class="stat-number" id="temporary-blocks">-</p>
                </div>
                <div class="stat-card">
                    <h3>Permanent Blocks</h3>
                    <p class="stat-number" id="permanent-blocks">-</p>
                </div>
                <div class="stat-card">
                    <h3>Premium IPs</h3>
                    <p class="stat-number" id="premium-ips-count">-</p>
                </div>
            </div>
            
            <button class="btn refresh-btn" onclick="loadIPData()">🔄 Refresh Data</button>
            
            <div class="ip-section">
                <h2>🚫 Blocked IPs</h2>
                <div id="blocked-ips" class="loading">
                    <p>Loading blocked IPs...</p>
                </div>
            </div>
            
            <div class="ip-section">
                <h2>⭐ Premium IPs</h2>
                <div id="premium-ips">
                    <p>Premium IPs are configured via environment variables (PREMIUM_IPS)</p>
                    <div id="premium-ips-list"></div>
                </div>
            </div>
            
            <div class="ip-section">
                <h2>🔑 API Keys</h2>
                <div id="api-keys">
                    <p>Valid API keys are configured via environment variables (VALID_API_KEYS)</p>
                    <div id="api-keys-list"></div>
                </div>
            </div>
        </main>
    </div>
    
    <!-- Block IP Modal -->
    <div id="blockIPModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal('blockIPModal')">&times;</span>
            <h3>Block IP Address</h3>
            <form id="blockIPForm">
                <div class="form-group">
                    <label>IP Address:</label>
                    <input type="text" id="blockIPAddress" required placeholder="192.168.1.100">
                </div>
                <div class="form-group">
                    <label>Block Level:</label>
                    <select id="blockLevel" required>
                        <option value="temporary">Temporary (30 minutes)</option>
                        <option value="extended">Extended (6 hours)</option>
                        <option value="permanent">Permanent (until manually unblocked)</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Reason:</label>
                    <textarea id="blockReason" rows="3" required placeholder="Reason for blocking this IP"></textarea>
                </div>
                <button type="submit" class="btn btn-danger">Block IP</button>
                <button type="button" class="btn btn-warning" onclick="closeModal('blockIPModal')">Cancel</button>
            </form>
        </div>
    </div>
    
    <script>
        // Configuration
        const API_BASE = window.location.origin;
        const ADMIN_API_KEY = 'astraverify-admin-2024';
        
        // Helper function to show messages
        function showMessage(message, type = 'success') {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = type === 'success' ? 'success-message' : 'error-message';
            messageDiv.textContent = message;
            messagesDiv.appendChild(messageDiv);
            
            // Auto-remove after 5 seconds
            setTimeout(() => {
                messageDiv.remove();
            }, 5000);
        }
        
        // Load blocked IPs
        async function loadBlockedIPs() {
            try {
                const response = await fetch(`${API_BASE}/api/admin/blocked-ips`, {
                    headers: {
                        'X-Admin-API-Key': ADMIN_API_KEY
                    }
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                const blockedIPsDiv = document.getElementById('blocked-ips');
                
                // Update statistics
                updateStatistics(data);
                
                if (data.blocked_ips && Object.keys(data.blocked_ips).length > 0) {
                    let html = '<div class="ip-list">';
                    
                    for (const [ip, info] of Object.entries(data.blocked_ips)) {
                        const blockedUntil = info.blocked_until ? new Date(info.blocked_until).toLocaleString() : 'Permanent';
                        const timeRemaining = info.blocked_until ? getTimeRemaining(info.blocked_until) : 'N/A';
                        const statusClass = info.level === 'permanent' ? 'permanent' : info.level === 'temporary' ? 'temporary' : 'blocked';
                        
                        html += `
                            <div class="ip-item ${statusClass}">
                                <div class="ip-info">
                                    <strong>${ip}</strong>
                                    <span class="status-badge status-${info.level}">${info.level.toUpperCase()}</span>
                                    <br><small>Reason: ${info.reason}</small>
                                    <br><small>Level: ${info.level}</small>
                                    <br><small>Blocked until: ${blockedUntil}</small>
                                    <br><small>Time remaining: ${timeRemaining}</small>
                                    <br><small>Blocked at: ${new Date(info.blocked_at).toLocaleString()}</small>
                                </div>
                                <div class="ip-actions">
                                    <button class="btn btn-success" onclick="unblockIP('${ip}')">Unblock</button>
                                    <button class="btn btn-info" onclick="viewIPAnalytics('${ip}')">Analytics</button>
                                </div>
                            </div>
                        `;
                    }
                    
                    html += '</div>';
                    blockedIPsDiv.innerHTML = html;
                } else {
                    blockedIPsDiv.innerHTML = '<p>No IPs are currently blocked.</p>';
                }
                
                blockedIPsDiv.classList.remove('loading');
                
            } catch (error) {
                console.error('Error loading blocked IPs:', error);
                document.getElementById('blocked-ips').innerHTML = 
                    '<p class="error-message">Error loading blocked IPs: ' + error.message + '</p>';
                document.getElementById('blocked-ips').classList.remove('loading');
            }
        }
        
        // Update statistics
        function updateStatistics(data) {
            if (data.blocked_ips) {
                const blockedIPs = Object.values(data.blocked_ips);
                const totalBlocked = blockedIPs.length;
                const temporaryBlocks = blockedIPs.filter(ip => ip.level === 'temporary').length;
                const permanentBlocks = blockedIPs.filter(ip => ip.level === 'permanent').length;
                
                document.getElementById('total-blocked').textContent = totalBlocked;
                document.getElementById('temporary-blocks').textContent = temporaryBlocks;
                document.getElementById('permanent-blocks').textContent = permanentBlocks;
            }
        }
        
        // Calculate time remaining
        function getTimeRemaining(blockedUntil) {
            const now = new Date();
            const until = new Date(blockedUntil);
            const diff = until - now;
            
            if (diff <= 0) {
                return 'Expired';
            }
            
            const hours = Math.floor(diff / (1000 * 60 * 60));
            const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            
            if (hours > 0) {
                return `${hours}h ${minutes}m`;
            } else {
                return `${minutes}m`;
            }
        }
        
        // Unblock an IP
        async function unblockIP(ip) {
            if (!confirm(`Are you sure you want to unblock IP ${ip}?`)) {
                return;
            }
            
            try {
                const response = await fetch(`${API_BASE}/api/admin/unblock-ip/${ip}`, {
                    method: 'POST',
                    headers: {
                        'X-Admin-API-Key': ADMIN_API_KEY
                    }
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                
                if (data.success) {
                    showMessage(`IP ${ip} has been unblocked successfully.`);
                    loadBlockedIPs(); // Refresh the list
                } else {
                    showMessage(`Failed to unblock IP ${ip}: ${data.message}`, 'error');
                }
                
            } catch (error) {
                console.error('Error unblocking IP:', error);
                showMessage(`Error unblocking IP ${ip}: ${error.message}`, 'error');
            }
        }
        
        // View IP analytics
        async function viewIPAnalytics(ip) {
            try {
                const response = await fetch(`${API_BASE}/api/admin/ip-analytics/${ip}`, {
                    headers: {
                        'X-Admin-API-Key': ADMIN_API_KEY
                    }
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                
                let analyticsHtml = `
                    <div class="ip-analytics">
                        <h4>Analytics for ${ip}</h4>
                        <p><strong>Total Requests:</strong> ${data.analytics?.total_requests || 'N/A'}</p>
                        <p><strong>Unique Domains:</strong> ${data.analytics?.unique_domains || 'N/A'}</p>
                        <p><strong>Error Count:</strong> ${data.analytics?.error_count || 'N/A'}</p>
                        <p><strong>Average Response Time:</strong> ${data.analytics?.avg_response_time || 'N/A'}ms</p>
                        <p><strong>Last Request:</strong> ${data.analytics?.last_request || 'N/A'}</p>
                        <p><strong>Abuse Score:</strong> ${data.abuse_score || 'N/A'}</p>
                        <p><strong>Risk Level:</strong> ${data.risk_level || 'N/A'}</p>
                    </div>
                `;
                
                // Show analytics in a modal or alert
                alert(`Analytics for ${ip}:\n\n` + 
                      `Total Requests: ${data.analytics?.total_requests || 'N/A'}\n` +
                      `Unique Domains: ${data.analytics?.unique_domains || 'N/A'}\n` +
                      `Error Count: ${data.analytics?.error_count || 'N/A'}\n` +
                      `Abuse Score: ${data.abuse_score || 'N/A'}\n` +
                      `Risk Level: ${data.risk_level || 'N/A'}`);
                
            } catch (error) {
                console.error('Error loading IP analytics:', error);
                showMessage(`Error loading analytics for ${ip}: ${error.message}`, 'error');
            }
        }
        
        // Load premium IPs from environment
        function loadPremiumIPs() {
            const premiumIPsDiv = document.getElementById('premium-ips-list');
            // This would need to be implemented on the backend to read environment variables
            premiumIPsDiv.innerHTML = '<p>Premium IPs: 127.0.0.1, ::1 (from environment)</p>';
        }
        
        // Load API keys from environment
        function loadAPIKeys() {
            const apiKeysDiv = document.getElementById('api-keys-list');
            // This would need to be implemented on the backend to read environment variables
            apiKeysDiv.innerHTML = '<p>API Keys: test-api-key-1, test-api-key-2 (from environment)</p>';
        }
        
        // Modal functions
        function closeModal(modalId) {
            document.getElementById(modalId).style.display = 'none';
        }
        
        // Load all IP data
        async function loadIPData() {
            await loadBlockedIPs();
            loadPremiumIPs();
            loadAPIKeys();
        }
        
        // Load data on page load
        document.addEventListener('DOMContentLoaded', function() {
            loadIPData();
        });
        
        // Auto-refresh every 30 seconds
        setInterval(loadBlockedIPs, 30000);
    </script>
</body>
</html>
"""

def create_admin_ui_routes(app):
    """Create admin UI routes"""
    
    @app.route('/admin/ui/login')
    def admin_ui_login():
        """Admin login page"""
        error = request.args.get('error')
        return render_template_string(ADMIN_LOGIN_TEMPLATE, error=error)
    
    @app.route('/admin/ui/dashboard')
    def admin_ui_dashboard():
        """Admin dashboard page"""
        # Get real blocked IP count
        try:
            from ip_blocker import IPBlocker
            ip_blocker = IPBlocker()
            blocked_ips = ip_blocker.get_blocked_ips()
            blocked_ips_count = len(blocked_ips)
        except:
            blocked_ips_count = 0
        
        user = {
            'name': 'Admin User',
            'email': 'admin@astraverify.com',
            'role': 'super_admin'
        }
        stats = {
            'total_domains': 150,
            'active_selectors': 45,
            'today_scans': 23,
            'blocked_ips': blocked_ips_count
        }
        return render_template_string(ADMIN_DASHBOARD_TEMPLATE, user=user, stats=stats)
    
    @app.route('/admin/ui/selectors/<domain>')
    def admin_ui_selectors(domain):
        """DKIM selector management page"""
        # Mock data for demonstration
        admin_selectors = [
            {
                'selector': 'selector1',
                'priority': 'high',
                'added_by': 'admin@astraverify.com',
                'verification_status': 'verified',
                'notes': 'Primary DKIM selector'
            },
            {
                'selector': 'selector2',
                'priority': 'medium',
                'added_by': 'admin@astraverify.com',
                'verification_status': 'failed',
                'notes': 'Backup selector'
            }
        ]
        
        discovered_selectors = [
            {
                'selector': 'google',
                'source': 'email_analysis',
                'usage_count': 15,
                'verification_status': 'verified',
                'discovery_date': '2024-01-15'
            }
        ]
        
        brute_force_selectors = {
            'total': 276,
            'sample': ['default', 'google', 'selector1', 'selector2', 'k1', 'dkim1', 'mailgun', 'sendgrid', 'zoho', 'yahoo']
        }
        
        return render_template_string(
            DKIM_SELECTOR_MANAGEMENT_TEMPLATE,
            domain=domain,
            admin_selectors=admin_selectors,
            discovered_selectors=discovered_selectors,
            brute_force_selectors=brute_force_selectors
        )
    
    @app.route('/admin/ui/ip-management')
    def admin_ui_ip_management():
        """IP management page"""
        # Mock data for demonstration
        user = {
            'name': 'Admin User',
            'email': 'admin@astraverify.com',
            'role': 'super_admin'
        }
        return render_template_string(IP_MANAGEMENT_TEMPLATE, user=user)
    
    return app
