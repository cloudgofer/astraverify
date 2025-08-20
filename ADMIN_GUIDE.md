# AstraVerify Admin Guide
## Enhanced Security Implementation & Management

**Version:** 2.1  
**Last Updated:** August 19, 2025  
**Environment:** PRODUCTION & STAGE  
**Status:** Production Ready ✅

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Security Features](#security-features)
3. [Environment Configuration](#environment-configuration)
4. [Deployment Procedures](#deployment-procedures)
5. [API Endpoints](#api-endpoints)
6. [Monitoring & Logging](#monitoring--logging)
7. [Troubleshooting](#troubleshooting)
8. [Security Best Practices](#security-best-practices)
9. [Emergency Procedures](#emergency-procedures)
10. [Contact Information](#contact-information)

---

## 🎯 Overview

AstraVerify STAGE environment has been enhanced with enterprise-grade security features including comprehensive input validation, rate limiting, security headers, and abuse prevention mechanisms.

### **Current Environment Status**

#### **Production Environment**
- **Backend URL**: `https://astraverify-backend-ml2mhibdvq-uc.a.run.app`
- **Frontend URL**: `https://astraverify-frontend-ml2mhibdvq-uc.a.run.app`
- **Environment**: Production
- **Security Level**: Enhanced (Enterprise Grade) - Production Optimized
- **Last Deployment**: August 19, 2025
- **Status**: ✅ Fully Operational

#### **Staging Environment**
- **Backend URL**: `https://astraverify-backend-staging-1098627686587.us-central1.run.app`
- **Frontend URL**: `https://astraverify-frontend-staging-ml2mhibdvq-uc.a.run.app`
- **Environment**: Staging
- **Security Level**: Enhanced (Enterprise Grade)
- **Last Deployment**: August 19, 2025

---

## 🔒 Security Features

### **1. Security Headers (OWASP Compliant)**
All responses include comprehensive security headers:

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https:; connect-src 'self' https:; frame-ancestors 'none';
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

### **2. Enhanced Rate Limiting**
Tier-based rate limiting with Redis backend:

| Tier | Requests/Minute | Requests/Hour | Requests/Day |
|------|----------------|---------------|--------------|
| Free | 10 | 100 | 1,000 |
| Authenticated | 30 | 500 | 5,000 |
| Premium | 100 | 2,000 | 20,000 |

### **3. Production-Optimized Abuse Detection**
Environment-based thresholds for optimal performance:

#### **Production Environment**
- **Rapid Requests**: 200 requests/minute (vs 50 in staging)
- **Repeated Domains**: 50 requests/hour (vs 20 in staging)
- **Error Spam**: 20 errors/5min (vs 10 in staging)
- **User Agent Patterns**: Excludes python/curl/wget patterns
- **Penalty Scores**: Reduced for production environment

#### **Staging Environment**
- **Rapid Requests**: 50 requests/minute
- **Repeated Domains**: 20 requests/hour
- **Error Spam**: 10 errors/5min
- **User Agent Patterns**: Includes all suspicious patterns
- **Penalty Scores**: Standard security levels

**Rate Limit Headers:**
```http
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 9
X-RateLimit-Reset: 1755624336
```

### **4. Input Validation**
Comprehensive validation that rejects:

- **IP Addresses**: `192.168.1.1` → 400 Error
- **XSS Attempts**: `<script>alert('xss')</script>` → 400 Error
- **SQL Injection**: `'; DROP TABLE users; --` → 400 Error
- **HTML Injection**: `<iframe src="...">` → 400 Error
- **Invalid Formats**: Empty domains, malformed domains → 400 Error

### **5. Abuse Prevention**
- **IP Blocking**: Automatic blocking of suspicious IPs
- **Request Fingerprinting**: Unique request identification
- **Suspicious Behavior Detection**: Bot detection, rapid requests
- **User Agent Validation**: Empty/suspicious user agents flagged
- **Environment-Based Thresholds**: Production-optimized settings
- **Admin Block Management**: Emergency clearing and individual IP management

### **6. Admin Authentication**
- **API Key**: `astraverify-admin-2024`
- **Header**: `X-Admin-API-Key: astraverify-admin-2024`
- **Endpoints**: All admin endpoints require authentication

---

## ⚙️ Environment Configuration

### **Environment Variables**
```bash
ENVIRONMENT=staging
ADMIN_API_KEY=astraverify-admin-2024
REDIS_URL=redis://localhost:6379
EMAIL_PASSWORD=[from GCP Secret Manager]
```

### **File Structure**
```
backend/
├── app_with_security.py          # Main application with enhanced security
├── app_enhanced_security.py      # Enhanced security implementation
├── Dockerfile                    # Updated to use app_with_security.py
├── requirements.txt              # Updated with security dependencies
├── scoring_engine.py             # Fixed null value handling
├── recommendation_engine.py      # Fixed method signatures
└── backup/                       # Backup directory for rollbacks
```

### **Dependencies**
```txt
flask==2.3.3
flask-cors==4.0.0
redis==4.6.0
flask-limiter==3.5.0
dns-resolver==2.4.2
google-cloud-firestore==2.11.1
google-cloud-secret-manager==2.16.4
```

---

## 🚀 Deployment Procedures

### **Standard Deployment**
```bash
# Deploy to STAGE
gcloud run deploy astraverify-backend-staging \
  --source backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ENVIRONMENT=staging,ADMIN_API_KEY=astraverify-admin-2024
```

### **Enhanced Security Deployment**
```bash
# Use the deployment script
./deploy_enhanced_security.sh
```

### **Rollback Procedure**
```bash
# Restore from backup
cp backup/local_20250819_081222/app_with_security.py backend/
cp backup/local_20250819_081222/requirements.txt backend/

# Redeploy
gcloud run deploy astraverify-backend-staging --source backend --platform managed --region us-central1 --allow-unauthenticated --set-env-vars ENVIRONMENT=staging,ADMIN_API_KEY=astraverify-admin-2024
```

---

## 🔌 API Endpoints

### **Public Endpoints**

#### **Health Check**
```http
GET /api/health
```
**Response:**
```json
{
  "status": "healthy",
  "environment": "staging",
  "timestamp": "2025-08-19T17:11:18.980583",
  "security_enabled": true,
  "enhanced_security": true,
  "rate_limiting": "enabled",
  "input_validation": "enhanced"
}
```

#### **Domain Check**
```http
GET /api/check?domain=example.com
```
**Security Features:**
- Input validation
- Rate limiting
- Abuse detection
- Comprehensive analysis

### **Admin Endpoints**

#### **Security Dashboard**
```http
GET /api/admin/security-dashboard
Headers: X-Admin-API-Key: astraverify-admin-2024
```
**Response:**
```json
{
  "environment": "staging",
  "total_requests": 8,
  "rate_limited_requests": 0,
  "top_requesting_ips": [
    {
      "ip": "50.145.12.2",
      "count": 8
    }
  ],
  "timestamp": "2025-08-19T17:24:48.291708"
}
```

#### **Blocked IPs**
```http
GET /api/admin/blocked-ips
Headers: X-Admin-API-Key: astraverify-admin-2024
```

#### **Block IP**
```http
POST /api/admin/block-ip/<ip_address>
Headers: X-Admin-API-Key: astraverify-admin-2024
```

#### **Unblock IP**
```http
POST /api/admin/unblock-ip/<ip_address>
Headers: X-Admin-API-Key: astraverify-admin-2024
```
**Response:**
```json
{
  "success": true,
  "message": "IP 192.168.1.100 unblocked"
}
```

#### **Clear All Blocks (Emergency)**
```http
POST /api/admin/clear-all-blocks
Headers: X-Admin-API-Key: astraverify-admin-2024
```
**Response:**
```json
{
  "success": true,
  "message": "All IP blocks and abuse detection data cleared",
  "cleared_ips": 5
}
```

#### **Reset Abuse Detection for Specific IP**
```http
POST /api/admin/reset-abuse-detection
Headers: X-Admin-API-Key: astraverify-admin-2024
Content-Type: application/json

{
  "ip": "192.168.1.100"
}
```
**Response:**
```json
{
  "success": true,
  "message": "Abuse detection reset for IP 192.168.1.100"
}
```

#### **IP Analytics**
```http
GET /api/admin/ip-analytics/<ip_address>
Headers: X-Admin-API-Key: astraverify-admin-2024
```

---

## 📊 Monitoring & Logging

### **Cloud Run Logs**
```bash
# View recent logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=astraverify-backend-staging" --limit=20 --format="table(timestamp,textPayload)"

# View specific revision logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=astraverify-backend-staging AND resource.labels.revision_name=astraverify-backend-staging-00025-2nj" --limit=10 --format="table(timestamp,textPayload)"
```

### **Key Log Messages**
- `Starting AstraVerify backend with ENHANCED security in staging environment`
- `Redis not available, using in-memory rate limiting`
- `IP blocked: [reason]`
- `Rate limit exceeded for [ip]`
- `Invalid domain format: [domain]`

### **Health Monitoring**
```bash
# Check service health
curl -I https://astraverify-backend-staging-1098627686587.us-central1.run.app/api/health

# Check security headers
curl -I https://astraverify-backend-staging-1098627686587.us-central1.run.app/api/health | grep -E "(X-Content-Type-Options|X-Frame-Options|X-XSS-Protection|Strict-Transport-Security|Content-Security-Policy)"
```

---

## 🔧 Troubleshooting

### **Common Issues & Solutions**

#### **1. Service Won't Start**
**Symptoms:** Container fails to start, port binding errors
**Solution:**
```bash
# Check Dockerfile entry point
cat backend/Dockerfile
# Should be: CMD ["python", "app_with_security.py"]

# Check port configuration
grep "app.run" backend/app_with_security.py
# Should be: port = int(os.environ.get('PORT', 5000))
```

#### **2. Security Headers Missing**
**Symptoms:** No security headers in responses
**Solution:**
```bash
# Verify enhanced security code is deployed
curl -I https://astraverify-backend-staging-1098627686587.us-central1.run.app/api/health

# Check if app_with_security.py contains enhanced code
grep -n "X-Content-Type-Options" backend/app_with_security.py
```

#### **3. Input Validation Not Working**
**Symptoms:** IP addresses or XSS attempts not rejected
**Solution:**
```bash
# Test input validation
curl -s -w "%{http_code}" "https://astraverify-backend-staging-1098627686587.us-central1.run.app/api/check?domain=192.168.1.1"
# Should return 400

# Check validation function
grep -n "validate_domain" backend/app_with_security.py
```

#### **4. Rate Limiting Errors**
**Symptoms:** TypeError with `>=` not supported between `NoneType` and `int`
**Solution:**
```bash
# Check rate limiting configuration
grep -A 10 "RATE_LIMIT_CONFIG" backend/app_with_security.py

# Verify Redis connection
grep -n "Redis not available" backend/app_with_security.py
```

#### **5. Recommendation Engine Errors**
**Symptoms:** TypeError with method signature mismatch
**Solution:**
```bash
# Check method calls
grep -n "generate_recommendations" backend/app_with_security.py

# Verify method signature in recommendation_engine.py
grep -A 5 "def generate_recommendations" backend/recommendation_engine.py
```

### **Testing Commands**
```bash
# Test enhanced security features
node test_enhanced_security.js

# Test comprehensive functionality
./run_stage_tests.sh

# Test specific security features
node test_security_features.js

# Test mobile responsiveness
node test_mobile_responsiveness.js
```

---

## 🛡️ Security Best Practices

### **Regular Security Checks**
1. **Daily**: Monitor admin dashboard for suspicious activity
2. **Weekly**: Review blocked IPs and analytics
3. **Monthly**: Update security dependencies
4. **Quarterly**: Security audit and penetration testing

### **Monitoring Checklist**
- [ ] Security headers present in all responses
- [ ] Rate limiting working correctly
- [ ] Input validation rejecting malicious inputs
- [ ] Admin endpoints requiring authentication
- [ ] No unauthorized access attempts
- [ ] Redis connection stable (if using)

### **Security Metrics**
- **Request Volume**: Monitor for unusual spikes
- **Blocked Requests**: Track blocked IPs and reasons
- **Rate Limit Hits**: Monitor rate limiting effectiveness
- **Error Rates**: Watch for security-related errors

### **Block Management Procedures**

#### **Daily Block Management**
```bash
# Check currently blocked IPs
curl -H "X-Admin-API-Key: astraverify-admin-2024" \
  "https://astraverify-backend-ml2mhibdvq-uc.a.run.app/api/admin/blocked-ips"

# Review blocked IP analytics
curl -H "X-Admin-API-Key: astraverify-admin-2024" \
  "https://astraverify-backend-ml2mhibdvq-uc.a.run.app/api/admin/ip-analytics/192.168.1.100"
```

#### **Emergency Block Clearing**
```bash
# Clear all blocks (use only in emergencies)
curl -X POST "https://astraverify-backend-ml2mhibdvq-uc.a.run.app/api/admin/clear-all-blocks" \
  -H "X-Admin-API-Key: astraverify-admin-2024" \
  -H "Content-Type: application/json"

# Reset abuse detection for specific IP
curl -X POST "https://astraverify-backend-ml2mhibdvq-uc.a.run.app/api/admin/reset-abuse-detection" \
  -H "X-Admin-API-Key: astraverify-admin-2024" \
  -H "Content-Type: application/json" \
  -d '{"ip": "192.168.1.100"}'
```

#### **Block Management Best Practices**
1. **Regular Review**: Check blocked IPs daily
2. **Legitimate IPs**: Unblock legitimate users immediately
3. **Pattern Analysis**: Look for patterns in blocked IPs
4. **Threshold Adjustment**: Adjust abuse detection thresholds if needed
5. **Documentation**: Keep records of all block management actions

---

## 🚨 Emergency Procedures

### **Service Down**
1. Check Cloud Run service status
2. Review recent deployment logs
3. Rollback to previous working revision if needed
4. Contact development team

### **Security Breach**
1. Immediately block suspicious IPs via admin endpoints
2. Review security dashboard for unusual activity
3. Check logs for unauthorized access attempts
4. Update admin API key if compromised
5. Notify security team

### **Production Environment Blocked**
1. **Immediate Action**: Clear all blocks using emergency endpoint
   ```bash
   curl -X POST "https://astraverify-backend-ml2mhibdvq-uc.a.run.app/api/admin/clear-all-blocks" \
     -H "X-Admin-API-Key: astraverify-admin-2024" \
     -H "Content-Type: application/json"
   ```
2. **Verify Resolution**: Check health endpoint
   ```bash
   curl "https://astraverify-backend-ml2mhibdvq-uc.a.run.app/api/health"
   ```
3. **Monitor**: Watch for legitimate traffic patterns
4. **Adjust Settings**: If needed, modify abuse detection thresholds
5. **Document**: Record the incident and resolution steps

### **Performance Issues**
1. Check rate limiting configuration
2. Monitor Redis connection (if using)
3. Review resource usage in Cloud Run
4. Scale up if necessary

### **Data Loss**
1. Check Firestore backup status
2. Review recent data operations
3. Restore from backup if needed
4. Investigate root cause

---

## 📞 Contact Information

### **Emergency Contacts**
- **Security Team**: security@astraverify.com
- **DevOps Team**: devops@astraverify.com
- **Development Team**: dev@astraverify.com

### **Documentation**
- **Technical Docs**: [Internal Wiki]
- **API Documentation**: [API Docs]
- **Security Guidelines**: [Security Wiki]

### **Support Channels**
- **Slack**: #astraverify-admin
- **Email**: admin@astraverify.com
- **Phone**: +1-555-ADMIN-01

---

## 📝 Change Log

### **Version 2.1 (August 19, 2025)**
- ✅ **NEW**: Admin block management endpoints added
- ✅ **NEW**: Emergency block clearing functionality
- ✅ **NEW**: Individual IP abuse detection reset
- ✅ **NEW**: Production-optimized abuse detection thresholds
- ✅ **NEW**: Environment-based security configuration
- ✅ Enhanced security features implemented
- ✅ Security headers added (OWASP compliant)
- ✅ Rate limiting with Redis backend
- ✅ Comprehensive input validation
- ✅ Admin authentication system
- ✅ Abuse prevention mechanisms
- ✅ Fixed scoring engine null value handling
- ✅ Fixed recommendation engine method signatures
- ✅ Updated Dockerfile for enhanced security
- ✅ Comprehensive testing suite implemented

### **Version 2.0 (August 19, 2025)**
- Enhanced security features implemented
- Security headers added (OWASP compliant)
- Rate limiting with Redis backend
- Comprehensive input validation
- Admin authentication system
- Abuse prevention mechanisms
- Fixed scoring engine null value handling
- Fixed recommendation engine method signatures
- Updated Dockerfile for enhanced security
- Comprehensive testing suite implemented

### **Version 1.0 (Previous)**
- Basic security implementation
- Standard rate limiting
- Basic input validation

---

## 🔄 Maintenance Schedule

### **Daily Tasks**
- [ ] Check service health
- [ ] Review security dashboard
- [ ] Monitor error logs

### **Weekly Tasks**
- [ ] Review blocked IPs
- [ ] Update security metrics
- [ ] Check dependency updates

### **Monthly Tasks**
- [ ] Security audit
- [ ] Performance review
- [ ] Backup verification

### **Quarterly Tasks**
- [ ] Penetration testing
- [ ] Security training
- [ ] Policy review

---

**Document Version:** 2.1  
**Last Updated:** August 19, 2025  
**Next Review:** September 19, 2025  
**Maintained By:** AstraVerify Admin Team
