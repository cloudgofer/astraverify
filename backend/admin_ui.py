from flask import Flask, render_template_string, request, jsonify, redirect, url_for
import os

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
                <li><a href="/admin/dashboard" class="active">Dashboard</a></li>
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
            </div>
            
            <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h3>Quick Actions</h3>
                <p><a href="/admin/domains">Manage Domains</a> | <a href="/admin/selectors">Manage DKIM Selectors</a> | <a href="/admin/analytics">View Analytics</a></p>
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
            
            fetch(`/admin/domains/${domain}/selectors`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
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
            fetch(`/admin/domains/${domain}/selectors/${selector}/test`)
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
                fetch(`/admin/domains/${domain}/selectors/${selector}`, {
                    method: 'DELETE'
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
        # Mock data for demonstration
        user = {
            'name': 'Admin User',
            'email': 'admin@astraverify.com',
            'role': 'super_admin'
        }
        stats = {
            'total_domains': 150,
            'active_selectors': 45,
            'today_scans': 23
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
    
    return app
