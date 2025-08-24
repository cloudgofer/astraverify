# Enhanced DKIM Selector Management System

## Overview

The Enhanced DKIM Selector Management System is a comprehensive solution for managing DKIM selectors with intelligent discovery, admin management, and performance optimization. This system provides a futuristic database schema that can adapt to evolving business requirements.

## Features

### 🎯 Core Features

- **Admin-Managed Selectors**: Add, remove, and manage DKIM selectors per domain
- **Discovered Selectors**: Automatically discover selectors from email analysis and brute force scanning
- **Intelligent Brute Force**: Smart subset selection for performance optimization
- **Priority-Based Scanning**: High-priority selectors checked first
- **Performance Analytics**: Track selector success rates and scan performance
- **Google OAuth Authentication**: Secure admin access with Google accounts
- **Role-Based Permissions**: Granular access control for different admin roles

### 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Input    │    │  Admin UI       │    │  Email Analysis │
│   (Web UI)      │    │  (Google OAuth) │    │  (Gmail API)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Enhanced DKIM Scanner                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │Selector Mgmt│  │Intelligent  │  │Performance  │            │
│  │             │  │Brute Force  │  │Analytics    │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Firestore Database                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │dkim_selectors│  │domain_scans │  │email_analysis│           │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

## Database Schema

### DKIM Selectors Collection (`dkim_selectors`)

```json
{
  "domain": "example.com",
  "admin_selectors": [
    {
      "selector": "selector1",
      "added_by": "admin@astraverify.com",
      "added_date": "2024-01-15T10:30:00Z",
      "notes": "Primary DKIM selector",
      "priority": "high",
      "status": "active",
      "verification_status": "verified",
      "last_tested": "2024-01-15T10:30:00Z",
      "test_results": {
        "valid": true,
        "dns_found": true,
        "valid_format": true,
        "record_preview": "v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3..."
      }
    }
  ],
  "discovered_selectors": [
    {
      "selector": "google",
      "source": "email_analysis",
      "discovery_date": "2024-01-15T10:30:00Z",
      "usage_count": 15,
      "verification_status": "verified",
      "last_used": "2024-01-15T10:30:00Z"
    }
  ],
  "last_updated": "2024-01-15T10:30:00Z"
}
```

## Components

### 1. DKIM Selector Manager (`dkim_selector_manager.py`)

**Key Features:**
- Load and save brute force selectors from file
- Manage admin-selectors per domain
- Track discovered selectors
- Intelligent selector prioritization
- Selector validation and testing

**Main Methods:**
```python
# Get comprehensive selector list for domain
get_domain_selectors(domain, custom_selector=None)

# Add admin-managed selector
add_admin_selector(domain, selector, notes, priority, added_by)

# Remove admin selector
remove_admin_selector(domain, selector)

# Add discovered selector
add_discovered_selector(domain, selector, source, verification_status)

# Test individual selector
_test_selector(domain, selector)
```

### 2. Enhanced DKIM Scanner (`enhanced_dkim_scanner.py`)

**Key Features:**
- Comprehensive domain scanning with all selector types
- Performance optimization with intelligent subset selection
- Detailed analytics and recommendations
- Quick scan mode for performance-critical scenarios

**Main Methods:**
```python
# Comprehensive scan
scan_domain_dkim(domain, custom_selector=None)

# Quick scan for performance
quick_scan(domain, custom_selector=None)

# Store discovered selectors
_store_discovered_selectors(domain, found_records)
```

### 3. Admin API (`admin_api.py`)

**Key Features:**
- Google OAuth 2.0 authentication
- Role-based access control
- JWT session management
- RESTful API endpoints for selector management

**Authentication Flow:**
1. User accesses admin interface
2. Redirected to Google OAuth
3. Google returns authorization code
4. Backend exchanges code for user info
5. Validates domain authorization
6. Creates JWT session token
7. User accesses admin features

**API Endpoints:**
```
GET  /admin/domains/{domain}/selectors     # Get selectors
POST /admin/domains/{domain}/selectors     # Add selector
DELETE /admin/domains/{domain}/selectors/{selector}  # Remove selector
GET  /admin/domains/{domain}/selectors/{selector}/test  # Test selector
POST /admin/domains/{domain}/scan          # Scan domain
GET  /admin/brute-force-selectors          # Get brute force list
PUT  /admin/brute-force-selectors          # Update brute force list
```

### 4. Admin UI (`admin_ui.py`)

**Key Features:**
- Simple HTML-based admin interface
- Google OAuth integration
- DKIM selector management interface
- Real-time selector testing

**Pages:**
- `/admin/ui/login` - Google OAuth login
- `/admin/ui/dashboard` - Admin dashboard
- `/admin/ui/selectors/{domain}` - Selector management

## Installation & Setup

### 1. Environment Setup

```bash
# Set environment variables
export ENVIRONMENT=local
export GOOGLE_OAUTH_CLIENT_ID=your-google-oauth-client-id
export GOOGLE_OAUTH_CLIENT_SECRET=your-google-oauth-client-secret
export JWT_SECRET_KEY=your-secret-key
export EMAIL_PASSWORD=your-email-password
```

### 2. Install Dependencies

```bash
pip install -r requirements_enhanced.txt
```

### 3. Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URIs:
   - `http://localhost:5000/admin/auth/callback` (local)
   - `https://yourdomain.com/admin/auth/callback` (production)

### 4. Run the Application

```bash
# Run enhanced backend
python app_enhanced_dkim.py

# Test the system
python test_enhanced_dkim.py
```

## Usage

### 1. Basic Domain Scanning

```python
from enhanced_dkim_scanner import enhanced_dkim_scanner

# Comprehensive scan
result = enhanced_dkim_scanner.scan_domain_dkim("example.com")

# Quick scan
result = enhanced_dkim_scanner.quick_scan("example.com")
```

### 2. Admin Selector Management

```python
from dkim_selector_manager import dkim_selector_manager

# Add admin selector
dkim_selector_manager.add_admin_selector(
    domain="example.com",
    selector="custom_selector",
    notes="Custom DKIM selector",
    priority="high",
    added_by="admin@astraverify.com"
)

# Get domain summary
summary = dkim_selector_manager.get_domain_selector_summary("example.com")
```

### 3. API Usage

```bash
# Check domain with enhanced DKIM
curl "http://localhost:5000/api/check?domain=example.com"

# Admin endpoints (requires authentication)
curl -H "Cookie: admin_token=your-jwt-token" \
     "http://localhost:5000/admin/domains/example.com/selectors"
```

## Priority System

The system uses a priority-based selector ordering:

1. **Custom Selector** (Priority 1) - User-provided selector
2. **Admin Selectors** (Priority 2-4) - High/Medium/Low priority
3. **Discovered Selectors** (Priority 5) - Verified discovered selectors
4. **Brute Force Selectors** (Priority 6) - Intelligent subset

## Performance Optimization

### Intelligent Brute Force

- **Common Selectors First**: `default`, `google`, `selector1`, etc.
- **Provider-Specific**: Based on detected email provider
- **Limited Subset**: Maximum 10 selectors for performance
- **Caching**: 1-hour cache for selector lists

### Scan Modes

- **Comprehensive Scan**: All available selectors (up to 15)
- **Quick Scan**: Limited to 5 selectors for speed
- **Progressive Mode**: Early results without DKIM, then complete

## Security Features

### Authentication & Authorization

- **Google OAuth 2.0**: Secure authentication
- **Domain Restriction**: Only `astraverify.com` users
- **Role-Based Access**: Super admin, domain admin, limited admin
- **JWT Sessions**: Secure session management
- **Permission System**: Granular access control

### Input Validation

- **Domain Validation**: Comprehensive domain format checking
- **Selector Validation**: Regex-based selector format validation
- **Malicious Pattern Detection**: Protection against injection attacks
- **Rate Limiting**: Protection against abuse

## Monitoring & Analytics

### Performance Metrics

- **Scan Duration**: Time taken for each scan
- **Success Rate**: Percentage of successful selector checks
- **Selector Sources**: Distribution by source type
- **Response Times**: Average DNS query times

### Recommendations

The system generates intelligent recommendations based on:

- **Missing Components**: Suggest adding missing security features
- **Performance Issues**: Optimize selector lists
- **Discovery Opportunities**: Add discovered selectors as admin-managed
- **Provider-Specific**: Tailored recommendations for email providers

## Testing

Run the comprehensive test suite:

```bash
python test_enhanced_dkim.py
```

The test suite covers:
- Selector manager functionality
- Enhanced scanner performance
- Quick scan mode
- Individual selector testing
- Error handling

## Future Enhancements

### Phase 2: Email Intelligence
- Gmail API integration for email analysis
- DKIM signature extraction from emails
- Email delivery status tracking
- Automatic selector discovery

### Phase 3: Machine Learning
- ML-based provider detection
- Predictive selector suggestions
- Performance optimization algorithms
- Anomaly detection

### Phase 4: Advanced Analytics
- Real-time dashboard
- Historical trend analysis
- Predictive analytics
- Automated reporting

## Troubleshooting

### Common Issues

1. **Firestore Connection**: Ensure Google Cloud credentials are set
2. **OAuth Configuration**: Verify Google OAuth client ID and secret
3. **DNS Resolution**: Check network connectivity and DNS settings
4. **Permission Errors**: Verify admin role and domain authorization

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Health Check

```bash
curl "http://localhost:5000/api/health"
```

## Contributing

1. Create feature branch from `main`
2. Implement changes with tests
3. Run test suite: `python test_enhanced_dkim.py`
4. Submit pull request with detailed description

## License

This project is part of the AstraVerify platform and follows the same licensing terms.

---

**Version**: 2.0.0  
**Last Updated**: January 2024  
**Status**: Phase 1 Complete - Ready for Local Testing
