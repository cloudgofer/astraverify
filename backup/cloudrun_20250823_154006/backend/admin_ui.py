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
                <li><a href="/admin/ui/domains">Domain Management</a></li>
                <li><a href="/admin/ui/selectors/example.com">DKIM Selectors</a></li>
                <li><a href="/admin/analytics/selectors">Analytics</a></li>
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
                <p><a href="/admin/ui/ip-management">Manage IPs</a> | <a href="/admin/ui/domains">Manage Domains</a> | <a href="/admin/ui/selectors/example.com">Manage DKIM Selectors</a> | <a href="/admin/analytics/selectors">View Analytics</a></p>
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
            
            // Use the new API endpoint
            fetch(`/admin/ui/selectors/${domain}/add`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    selector: selector,
                    priority: priority,
                    notes: notes
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    alert(`Selector '${selector}' added successfully to ${domain}!`);
                    closeModal('addSelectorModal');
                    
                    // Add to the admin selectors list dynamically
                    const adminSelectorsDiv = document.getElementById('admin-selectors');
                    const statusClass = data.selector.verification_status === 'verified' ? 'verified' : 'failed';
                    const newSelectorHtml = `
                        <div class="selector-item ${statusClass}">
                            <strong>${selector}</strong> (${priority})
                            <br><small>Added by: ${data.selector.added_by} | Status: ${data.selector.verification_status}</small>
                            <br><small>Notes: ${notes}</small>
                            <div style="margin-top: 10px;">
                                <button class="btn btn-success" onclick="testSelector('${selector}')">Test</button>
                                <button class="btn btn-danger" onclick="removeSelector('${selector}')">Remove</button>
                            </div>
                        </div>
                    `;
                    adminSelectorsDiv.insertAdjacentHTML('beforeend', newSelectorHtml);
                    
                    // Clear the form
                    document.getElementById('selectorName').value = '';
                    document.getElementById('selectorPriority').value = 'medium';
                    document.getElementById('selectorNotes').value = '';
                } else {
                    alert('Failed to add selector: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Error adding selector:', error);
                alert('Error adding selector: ' + error.message);
            });
        });
        
        function testSelector(selector) {
            fetch(`/admin/ui/selectors/${domain}/test/${selector}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        if (data.test_result.valid) {
                            alert(`Selector ${selector} is valid! Status updated to verified.`);
                            // Update the UI to show verified status
                            location.reload();
                        } else {
                            alert(`Selector ${selector} is invalid: ${data.test_result.error}`);
                        }
                    } else {
                        alert('Failed to test selector: ' + (data.error || 'Unknown error'));
                    }
                })
                .catch(error => {
                    console.error('Error testing selector:', error);
                    alert('Error testing selector: ' + error.message);
                });
        }
        
        function removeSelector(selector) {
            if (confirm(`Are you sure you want to remove selector '${selector}'?`)) {
                fetch(`/admin/ui/selectors/${domain}/remove/${selector}`, {
                    method: 'DELETE'
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        alert('Selector removed successfully!');
                        location.reload();
                    } else {
                        alert('Failed to remove selector: ' + (data.error || 'Unknown error'));
                    }
                })
                .catch(error => {
                    console.error('Error removing selector:', error);
                    alert('Error removing selector: ' + error.message);
                });
            }
        }
        
        function scanDomain() {
            if (confirm(`Scan domain: ${domain}?`)) {
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
        }
        
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
            
            // Use the new API endpoint
            fetch(`/admin/ui/selectors/${domain}/add`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    selector: selector,
                    priority: priority,
                    notes: notes
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    alert(`Selector '${selector}' added successfully to ${domain}!`);
                    closeModal('addSelectorModal');
                    
                    // Add to the admin selectors list dynamically
                    const adminSelectorsDiv = document.getElementById('admin-selectors');
                    const statusClass = data.selector.verification_status === 'verified' ? 'verified' : 'failed';
                    const newSelectorHtml = `
                        <div class="selector-item ${statusClass}">
                            <strong>${selector}</strong> (${priority})
                            <br><small>Added by: ${data.selector.added_by} | Status: ${data.selector.verification_status}</small>
                            <br><small>Notes: ${notes}</small>
                            <div style="margin-top: 10px;">
                                <button class="btn btn-success" onclick="testSelector('${selector}')">Test</button>
                                <button class="btn btn-danger" onclick="removeSelector('${selector}')">Remove</button>
                            </div>
                        </div>
                    `;
                    adminSelectorsDiv.insertAdjacentHTML('beforeend', newSelectorHtml);
                    
                    // Clear the form
                    document.getElementById('selectorName').value = '';
                    document.getElementById('selectorPriority').value = 'medium';
                    document.getElementById('selectorNotes').value = '';
                } else {
                    alert('Failed to add selector: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Error adding selector:', error);
                alert('Error adding selector: ' + error.message);
            });
        });
    </script>
</body>
</html>
"""

DOMAIN_MANAGEMENT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AstraVerify Admin - Domain Management</title>
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
        .domain-section { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .domain-item { border: 1px solid #ddd; padding: 15px; margin-bottom: 10px; border-radius: 4px; display: flex; justify-content: space-between; align-items: center; }
        .domain-info { flex: 1; }
        .domain-actions { display: flex; gap: 10px; }
        .btn { padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
        .btn-primary { background: #007bff; color: white; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-success { background: #28a745; color: white; }
        .btn-warning { background: #ffc107; color: black; }
        .btn-info { background: #17a2b8; color: white; }
        .status-badge { padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }
        .status-active { background: #28a745; color: white; }
        .status-inactive { background: #6c757d; color: white; }
        .status-verified { background: #28a745; color: white; }
        .status-pending { background: #ffc107; color: black; }
        .status-failed { background: #dc3545; color: white; }
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
                <li><a href="/admin/ui/ip-management">IP Management</a></li>
                <li><a href="/admin/ui/domains" class="active">Domain Management</a></li>
                <li><a href="/admin/ui/selectors/example.com">DKIM Selectors</a></li>
                <li><a href="/admin/analytics/selectors">Analytics</a></li>
            </ul>
            
            <div style="margin-top: 30px;">
                <a href="/admin/logout" class="logout-btn">Logout</a>
            </div>
        </nav>
        
        <main class="admin-main">
            <h1>🌐 Domain Management Dashboard</h1>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>Total Domains</h3>
                    <p class="stat-number">{{ domains|length }}</p>
                </div>
                <div class="stat-card">
                    <h3>Active Domains</h3>
                    <p class="stat-number">{{ domains|selectattr('status', 'equalto', 'active')|list|length }}</p>
                </div>
                <div class="stat-card">
                    <h3>Verified DKIM</h3>
                    <p class="stat-number">{{ domains|selectattr('dkim_status', 'equalto', 'verified')|list|length }}</p>
                </div>
            </div>
            
            <div class="domain-section">
                <h2>📋 Managed Domains</h2>
                <button class="btn btn-success" onclick="showAddDomainModal()">+ Add Domain</button>
                
                <div id="domains-list">
                    {% for domain in domains %}
                    <div class="domain-item">
                        <div class="domain-info">
                            <strong>{{ domain.domain }}</strong>
                            <span class="status-badge status-{{ domain.status }}">{{ domain.status.upper() }}</span>
                            <span class="status-badge status-{{ domain.dkim_status }}">{{ domain.dkim_status.upper() }}</span>
                            <br><small>Selectors: {{ domain.selectors_count }} | Last Scan: {{ domain.last_scan }}</small>
                        </div>
                        <div class="domain-actions">
                            <a href="/admin/ui/selectors/{{ domain.domain }}" class="btn btn-primary">Manage Selectors</a>
                            <button class="btn btn-info" onclick="scanDomain('{{ domain.domain }}')">Scan</button>
                            <button class="btn btn-warning" onclick="editDomain('{{ domain.domain }}')">Edit</button>
                            <button class="btn btn-danger" onclick="removeDomain('{{ domain.domain }}')">Remove</button>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            
            <div class="domain-section">
                <h2>🔍 System Brute Force Selectors</h2>
                <p>These selectors are used across all domains for DKIM discovery</p>
                <button class="btn btn-primary" onclick="showBruteForceModal()">Edit Brute Force List</button>
                
                <div id="brute-force-selectors">
                    <p><strong>Total:</strong> {{ brute_force_selectors.total }} selectors</p>
                    <p><strong>Sample:</strong> {{ ', '.join(brute_force_selectors.sample) }}</p>
                </div>
            </div>
        </main>
    </div>
    
    <!-- Brute Force Selectors Modal -->
    <div id="bruteForceModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal('bruteForceModal')">&times;</span>
            <h3>Edit Brute Force Selectors</h3>
            <p>These selectors are used across all domains for DKIM discovery</p>
            <form id="bruteForceForm" onsubmit="handleBruteForceSubmit(event)">
                <div class="form-group">
                    <label>Selectors (one per line):</label>
                    <textarea id="bruteForceSelectors" rows="15" placeholder="default&#10;google&#10;selector1&#10;selector2&#10;k1&#10;dkim1&#10;mailgun&#10;sendgrid&#10;zoho&#10;yahoo">{{ '\\n'.join(brute_force_selectors.sample) }}</textarea>
                </div>
                <button type="submit" class="btn btn-primary">Save Changes</button>
                <button type="button" class="btn btn-warning" onclick="closeModal('bruteForceModal')">Cancel</button>
            </form>
        </div>
    </div>
    
    <script>
        // Domain Management Functions
        function showAddDomainModal() {
            const domain = prompt('Enter domain name (e.g., example.com):');
            if (domain && domain.trim()) {
                addDomain(domain.trim());
            }
        }
        
        function addDomain(domain) {
            fetch('/admin/ui/domains/add', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    domain: domain
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    alert(`Domain '${domain}' added successfully!`);
                    location.reload();
                } else {
                    alert('Failed to add domain: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Error adding domain:', error);
                alert('Error adding domain: ' + error.message);
            });
        }
        
        function scanDomain(domain) {
            if (confirm(`Scan domain: ${domain}?`)) {
                fetch(`/admin/ui/domains/scan/${domain}`, {
                    method: 'POST'
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        alert(`Domain '${domain}' scanned successfully!\\nSelectors found: ${data.scan_results.selectors_found}\\nDKIM status: ${data.scan_results.dkim_status}`);
                        location.reload();
                    } else {
                        alert('Failed to scan domain: ' + (data.error || 'Unknown error'));
                    }
                })
                .catch(error => {
                    console.error('Error scanning domain:', error);
                    alert('Error scanning domain: ' + error.message);
                });
            }
        }
        
        function editDomain(domain) {
            alert(`Edit domain functionality coming soon for: ${domain}`);
        }
        
        function removeDomain(domain) {
            if (confirm(`Are you sure you want to remove domain: ${domain}?\\nThis will also remove all associated selectors.`)) {
                fetch(`/admin/ui/domains/remove/${domain}`, {
                    method: 'DELETE'
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        alert(`Domain '${domain}' removed successfully!`);
                        location.reload();
                    } else {
                        alert('Failed to remove domain: ' + (data.error || 'Unknown error'));
                    }
                })
                .catch(error => {
                    console.error('Error removing domain:', error);
                    alert('Error removing domain: ' + error.message);
                });
            }
        }
        
        // Modal Functions
        function showBruteForceModal() {
            document.getElementById('bruteForceModal').style.display = 'block';
        }
        
        function closeModal(modalId) {
            document.getElementById(modalId).style.display = 'none';
        }
        
        function handleBruteForceSubmit(event) {
            event.preventDefault();
            
            const selectorsText = document.getElementById('bruteForceSelectors').value;
            const selectors = selectorsText.split('\\n').filter(s => s.trim() !== '');
            
            fetch('/admin/ui/brute-force-selectors', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    selectors: selectors
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    alert(`Brute force selectors updated successfully!\\nTotal selectors: ${data.total_selectors}`);
                    closeModal('bruteForceModal');
                    location.reload();
                } else {
                    alert('Failed to update brute force selectors: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Error updating brute force selectors:', error);
                alert('Error updating brute force selectors: ' + error.message);
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
                <li><a href="/admin/ui/domains">Domain Management</a></li>
                <li><a href="/admin/ui/selectors/example.com">DKIM Selectors</a></li>
                <li><a href="/admin/analytics/selectors">Analytics</a></li>
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
                <div id="blocked-ips">
                    <button class="btn btn-danger" onclick="showBlockIPModal()">🚫 Block New IP</button>
                    <div id="blocked-ips-list" class="loading">
                        <p>Loading blocked IPs...</p>
                    </div>
                </div>
            </div>
            
            <div class="ip-section">
                <h2>⭐ Premium IPs</h2>
                <div id="premium-ips">
                    <button class="btn btn-success" onclick="showAddPremiumIPModal()">+ Add Premium IP</button>
                    <button class="btn btn-info" onclick="loadPremiumIPs()">🔄 Refresh</button>
                    <div id="premium-ips-list" class="loading">
                        <p>Loading premium IPs...</p>
                    </div>
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
            <form id="blockIPForm" onsubmit="handleBlockIPSubmit(event)">
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
    
    <!-- Add Premium IP Modal -->
    <div id="addPremiumIPModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal('addPremiumIPModal')">&times;</span>
            <h3>Add Premium IP Address</h3>
            <form id="addPremiumIPForm" onsubmit="handleAddPremiumIPSubmit(event)">
                <div class="form-group">
                    <label>IP Address:</label>
                    <input type="text" id="premiumIPAddress" required placeholder="192.168.1.100">
                </div>
                <div class="form-group">
                    <label>Notes (Optional):</label>
                    <textarea id="premiumIPNotes" rows="3" placeholder="Notes about this premium IP"></textarea>
                </div>
                <button type="submit" class="btn btn-success">Add Premium IP</button>
                <button type="button" class="btn btn-warning" onclick="closeModal('addPremiumIPModal')">Cancel</button>
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
                const response = await fetch(`${API_BASE}/admin/ip-blocks`, {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
                    }
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                const blockedIPsDiv = document.getElementById('blocked-ips-list');
                
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
                                    <button class="btn btn-warning" onclick="extendBlock('${ip}')">Extend</button>
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
                document.getElementById('blocked-ips-list').innerHTML = 
                    '<p class="error-message">Error loading blocked IPs: ' + error.message + '</p>';
                document.getElementById('blocked-ips-list').classList.remove('loading');
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
                const response = await fetch(`${API_BASE}/admin/ip-blocks/${ip}`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
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
        
        // Extend block duration
        async function extendBlock(ip) {
            const additionalHours = prompt(`Enter additional hours to extend block for ${ip}:`, '6');
            
            if (!additionalHours || isNaN(additionalHours) || additionalHours <= 0) {
                showMessage('Please enter a valid number of hours', 'error');
                return;
            }
            
            try {
                const response = await fetch(`${API_BASE}/admin/ip-blocks/${ip}/extend`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        additional_hours: parseInt(additionalHours)
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                
                if (data.success) {
                    showMessage(`IP ${ip} block extended by ${additionalHours} hours.`);
                    loadBlockedIPs(); // Refresh the list
                } else {
                    showMessage(`Failed to extend block for IP ${ip}: ${data.message}`, 'error');
                }
                
            } catch (error) {
                console.error('Error extending block:', error);
                showMessage(`Error extending block for IP ${ip}: ${error.message}`, 'error');
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
        
        // Load premium IPs from API
        async function loadPremiumIPs() {
            try {
                const response = await fetch(`${API_BASE}/admin/premium-ips`, {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
                    }
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                const premiumIPsDiv = document.getElementById('premium-ips-list');
                
                if (data.premium_ips && data.premium_ips.length > 0) {
                    let html = '<div class="ip-list">';
                    
                    for (const ip of data.premium_ips) {
                        html += `
                            <div class="ip-item premium">
                                <div class="ip-info">
                                    <strong>${ip}</strong>
                                    <span class="status-badge status-premium">PREMIUM</span>
                                    <br><small>Added via Admin UI</small>
                                </div>
                                <div class="ip-actions">
                                    <button class="btn btn-danger" onclick="removePremiumIP('${ip}')">Remove</button>
                                </div>
                            </div>
                        `;
                    }
                    
                    html += '</div>';
                    premiumIPsDiv.innerHTML = html;
                } else {
                    premiumIPsDiv.innerHTML = '<p>No premium IPs configured.</p>';
                }
                
                // Update premium IP count in statistics
                document.getElementById('premium-ips-count').textContent = data.total_premium || 0;
                
                premiumIPsDiv.classList.remove('loading');
                
            } catch (error) {
                console.error('Error loading premium IPs:', error);
                document.getElementById('premium-ips-list').innerHTML = 
                    '<p class="error-message">Error loading premium IPs: ' + error.message + '</p>';
                document.getElementById('premium-ips-list').classList.remove('loading');
            }
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
        
        function showBlockIPModal() {
            document.getElementById('blockIPModal').style.display = 'block';
        }
        
        // Handle block IP form submission
        function handleBlockIPSubmit(event) {
            event.preventDefault();
            
            const ip = document.getElementById('blockIPAddress').value;
            const level = document.getElementById('blockLevel').value;
            const reason = document.getElementById('blockReason').value;
            
            if (!ip || !level || !reason) {
                showMessage('Please fill in all fields', 'error');
                return;
            }
            
            // Validate IP format
            const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
            if (!ipRegex.test(ip)) {
                showMessage('Please enter a valid IP address', 'error');
                return;
            }
            
            blockIP(ip, level, reason);
        }
        
        // Block an IP
        async function blockIP(ip, level, reason) {
            try {
                const response = await fetch(`${API_BASE}/admin/ip-blocks/${ip}`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        level: level,
                        reason: reason
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                
                if (data.success) {
                    showMessage(`IP ${ip} has been blocked successfully with level ${level}.`);
                    closeModal('blockIPModal');
                    loadBlockedIPs(); // Refresh the list
                } else {
                    showMessage(`Failed to block IP ${ip}: ${data.message}`, 'error');
                }
                
            } catch (error) {
                console.error('Error blocking IP:', error);
                showMessage(`Error blocking IP ${ip}: ${error.message}`, 'error');
            }
        }
        
        // Load all IP data
        async function loadIPData() {
            await loadBlockedIPs();
            loadPremiumIPs();
            loadAPIKeys();
        }
        
        // Premium IP Management Functions
        
        // Show add premium IP modal
        function showAddPremiumIPModal() {
            document.getElementById('addPremiumIPModal').style.display = 'block';
        }
        
        // Handle add premium IP form submission
        function handleAddPremiumIPSubmit(event) {
            event.preventDefault();
            
            const ip = document.getElementById('premiumIPAddress').value;
            const notes = document.getElementById('premiumIPNotes').value;
            
            if (!ip) {
                showMessage('Please enter an IP address', 'error');
                return;
            }
            
            // Validate IP format
            const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
            if (!ipRegex.test(ip)) {
                showMessage('Please enter a valid IP address', 'error');
                return;
            }
            
            addPremiumIP(ip, notes);
        }
        
        // Add a premium IP
        async function addPremiumIP(ip, notes) {
            try {
                const response = await fetch(`${API_BASE}/admin/premium-ips`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        ip: ip,
                        notes: notes
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                
                if (data.success) {
                    showMessage(`Premium IP ${ip} added successfully.`);
                    closeModal('addPremiumIPModal');
                    loadPremiumIPs(); // Refresh the list
                } else {
                    showMessage(`Failed to add premium IP ${ip}: ${data.message}`, 'error');
                }
                
            } catch (error) {
                console.error('Error adding premium IP:', error);
                showMessage(`Error adding premium IP ${ip}: ${error.message}`, 'error');
            }
        }
        
        // Remove a premium IP
        async function removePremiumIP(ip) {
            if (!confirm(`Are you sure you want to remove premium IP ${ip}?`)) {
                return;
            }
            
            try {
                const response = await fetch(`${API_BASE}/admin/premium-ips/${ip}`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
                    }
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                
                if (data.success) {
                    showMessage(`Premium IP ${ip} removed successfully.`);
                    loadPremiumIPs(); // Refresh the list
                } else {
                    showMessage(`Failed to remove premium IP ${ip}: ${data.message}`, 'error');
                }
                
            } catch (error) {
                console.error('Error removing premium IP:', error);
                showMessage(`Error removing premium IP ${ip}: ${error.message}`, 'error');
            }
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
    
    # In-memory storage for local development
    _local_selectors = {}
    _local_domains = [
        {
            'domain': 'astraverify.com',
            'status': 'active',
            'selectors_count': 5,
            'last_scan': '2024-01-15 10:30:00',
            'dkim_status': 'verified'
        },
        {
            'domain': 'example.com',
            'status': 'active',
            'selectors_count': 3,
            'last_scan': '2024-01-14 15:45:00',
            'dkim_status': 'pending'
        },
        {
            'domain': 'test.org',
            'status': 'inactive',
            'selectors_count': 0,
            'last_scan': '2024-01-10 09:20:00',
            'dkim_status': 'failed'
        }
    ]
    _local_brute_force_selectors = ['default', 'google', 'selector1', 'selector2', 'k1', 'dkim1', 'mailgun', 'sendgrid', 'zoho', 'yahoo']
    
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
    
    @app.route('/admin/ui/domains')
    def admin_ui_domains():
        """Domain management page"""
        # Update selector counts for domains
        for domain in _local_domains:
            domain['selectors_count'] = len(_local_selectors.get(domain['domain'], []))
        
        brute_force_selectors = {
            'total': len(_local_brute_force_selectors),
            'sample': _local_brute_force_selectors[:10]  # Show first 10
        }
        
        user = {
            'name': 'Local Admin User',
            'email': 'admin@astraverify.com',
            'role': 'super_admin'
        }
        
        return render_template_string(DOMAIN_MANAGEMENT_TEMPLATE, user=user, domains=_local_domains, brute_force_selectors=brute_force_selectors)
    
    @app.route('/admin/ui/selectors/<domain>')
    def admin_ui_selectors(domain):
        """DKIM selector management page"""
        # Get selectors from local storage or use defaults
        if domain not in _local_selectors:
            _local_selectors[domain] = [
                {
                    'selector': 'selector1',
                    'priority': 'high',
                    'added_by': 'admin@astraverify.com',
                    'verification_status': 'pending',
                    'notes': 'Primary DKIM selector'
                },
                {
                    'selector': 'selector2',
                    'priority': 'medium',
                    'added_by': 'admin@astraverify.com',
                    'verification_status': 'pending',
                    'notes': 'Backup selector'
                }
            ]
        
        admin_selectors = _local_selectors[domain]
        
        discovered_selectors = [
            {
                'selector': 'google',
                'source': 'email_analysis',
                'usage_count': 15,
                'verification_status': 'verified',
                'discovery_date': '2024-01-15'
            }
        ]
        
        return render_template_string(
            DKIM_SELECTOR_MANAGEMENT_TEMPLATE,
            domain=domain,
            admin_selectors=admin_selectors,
            discovered_selectors=discovered_selectors
        )
    
    # API endpoints for selector management
    @app.route('/admin/ui/selectors/<domain>/add', methods=['POST'])
    def add_selector_api(domain):
        """API endpoint to add a selector"""
        try:
            data = request.get_json()
            selector = data.get('selector')
            priority = data.get('priority', 'medium')
            notes = data.get('notes', '')
            
            if not selector:
                return jsonify({"success": False, "error": "Selector name is required"}), 400
            
            # Initialize domain if not exists
            if domain not in _local_selectors:
                _local_selectors[domain] = []
            
            # Check if selector already exists
            if any(s['selector'] == selector for s in _local_selectors[domain]):
                return jsonify({"success": False, "error": "Selector already exists"}), 400
            
            # Add new selector
            new_selector = {
                'selector': selector,
                'priority': priority,
                'added_by': 'admin@astraverify.com',
                'verification_status': 'pending',
                'notes': notes
            }
            
            _local_selectors[domain].append(new_selector)
            
            return jsonify({
                "success": True,
                "message": f"Selector '{selector}' added successfully",
                "selector": new_selector
            })
            
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    
    @app.route('/admin/ui/selectors/<domain>/remove/<selector>', methods=['DELETE'])
    def remove_selector_api(domain, selector):
        """API endpoint to remove a selector"""
        try:
            if domain not in _local_selectors:
                return jsonify({"success": False, "error": "Domain not found"}), 404
            
            # Find and remove selector
            original_length = len(_local_selectors[domain])
            _local_selectors[domain] = [s for s in _local_selectors[domain] if s['selector'] != selector]
            
            if len(_local_selectors[domain]) == original_length:
                return jsonify({"success": False, "error": "Selector not found"}), 404
            
            return jsonify({
                "success": True,
                "message": f"Selector '{selector}' removed successfully"
            })
            
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    
    @app.route('/admin/ui/selectors/<domain>/test/<selector>', methods=['GET'])
    def test_selector_api(domain, selector):
        """API endpoint to test a selector"""
        try:
            # Simulate selector testing
            import random
            is_valid = random.choice([True, False])  # Random result for demo
            
            if is_valid:
                # Update selector status to verified
                if domain in _local_selectors:
                    for s in _local_selectors[domain]:
                        if s['selector'] == selector:
                            s['verification_status'] = 'verified'
                            break
            
            return jsonify({
                "success": True,
                "test_result": {
                    "valid": is_valid,
                    "error": None if is_valid else "DKIM record not found"
                }
            })
            
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    
    # API endpoints for domain management
    @app.route('/admin/ui/domains/add', methods=['POST'])
    def add_domain_api():
        """API endpoint to add a domain"""
        try:
            data = request.get_json()
            domain = data.get('domain')
            
            if not domain:
                return jsonify({"success": False, "error": "Domain name is required"}), 400
            
            # Check if domain already exists
            if any(d['domain'] == domain for d in _local_domains):
                return jsonify({"success": False, "error": "Domain already exists"}), 400
            
            # Add new domain
            new_domain = {
                'domain': domain,
                'status': 'active',
                'selectors_count': 0,
                'last_scan': 'Never',
                'dkim_status': 'pending'
            }
            
            _local_domains.append(new_domain)
            
            return jsonify({
                "success": True,
                "message": f"Domain '{domain}' added successfully",
                "domain": new_domain
            })
            
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    
    @app.route('/admin/ui/domains/remove/<domain>', methods=['DELETE'])
    def remove_domain_api(domain):
        """API endpoint to remove a domain"""
        try:
            # Find and remove domain
            original_length = len(_local_domains)
            _local_domains[:] = [d for d in _local_domains if d['domain'] != domain]
            
            if len(_local_domains) == original_length:
                return jsonify({"success": False, "error": "Domain not found"}), 404
            
            # Also remove associated selectors
            if domain in _local_selectors:
                del _local_selectors[domain]
            
            return jsonify({
                "success": True,
                "message": f"Domain '{domain}' removed successfully"
            })
            
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    
    @app.route('/admin/ui/domains/scan/<domain>', methods=['POST'])
    def scan_domain_api(domain):
        """API endpoint to scan a domain"""
        try:
            # Find domain
            domain_obj = next((d for d in _local_domains if d['domain'] == domain), None)
            if not domain_obj:
                return jsonify({"success": False, "error": "Domain not found"}), 404
            
            # Simulate scanning
            import random
            from datetime import datetime
            
            # Update domain with scan results
            domain_obj['last_scan'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            domain_obj['selectors_count'] = len(_local_selectors.get(domain, []))
            domain_obj['dkim_status'] = random.choice(['verified', 'pending', 'failed'])
            
            return jsonify({
                "success": True,
                "message": f"Domain '{domain}' scanned successfully",
                "scan_results": {
                    "selectors_found": domain_obj['selectors_count'],
                    "dkim_status": domain_obj['dkim_status'],
                    "scan_time": domain_obj['last_scan']
                }
            })
            
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    
    @app.route('/admin/ui/brute-force-selectors', methods=['PUT'])
    def update_brute_force_selectors_api():
        """API endpoint to update brute force selectors"""
        try:
            data = request.get_json()
            selectors = data.get('selectors', [])
            
            if not isinstance(selectors, list):
                return jsonify({"success": False, "error": "Selectors must be a list"}), 400
            
            # Update global brute force selectors
            global _local_brute_force_selectors
            _local_brute_force_selectors = selectors
            
            return jsonify({
                "success": True,
                "message": f"Updated {len(selectors)} brute force selectors",
                "total_selectors": len(selectors)
            })
            
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    
    @app.route('/admin/ui/ip-management')
    def admin_ui_ip_management():
        """IP management page"""
        import os
        environment = os.environ.get('ENVIRONMENT', 'local')
        
        if environment == 'local':
            # Local development - bypass authentication like the dashboard
            user = {
                'name': 'Local Admin User',
                'email': 'admin@astraverify.com',
                'role': 'super_admin'
            }
            return render_template_string(IP_MANAGEMENT_TEMPLATE, user=user)
        
        # Production/Staging - check for admin token
        token = request.cookies.get('admin_token')
        
        if not token:
            return redirect('/admin/ui/login')
        
        # Validate token (simplified - in production you'd use the session manager)
        try:
            from admin_api import session_manager
            is_valid, payload = session_manager.validate_session(token)
            
            if not is_valid:
                return redirect('/admin/ui/login')
            
            user = {
                'name': payload.get('name', 'Admin User'),
                'email': payload.get('email', 'admin@astraverify.com'),
                'role': payload.get('role', 'super_admin')
            }
            
        except Exception as e:
            # Fallback to mock data for development
            user = {
                'name': 'Admin User',
                'email': 'admin@astraverify.com',
                'role': 'super_admin'
            }
        
        return render_template_string(IP_MANAGEMENT_TEMPLATE, user=user)
    
    return app
