# AstraVerify Admin Quick Reference
## Essential Commands & Information

**Version:** 2.0 | **Last Updated:** August 19, 2025 | **Environment:** STAGE

---

## 🚀 **Quick Commands**

### **Health Check**
```bash
# Check service health
curl -I https://astraverify-backend-staging-1098627686587.us-central1.run.app/api/health

# Check security headers
curl -I https://astraverify-backend-staging-1098627686587.us-central1.run.app/api/health | grep -E "(X-Content-Type-Options|X-Frame-Options|X-XSS-Protection)"
```

### **Deployment**
```bash
# Standard deployment
gcloud run deploy astraverify-backend-staging --source backend --platform managed --region us-central1 --allow-unauthenticated --set-env-vars ENVIRONMENT=staging,ADMIN_API_KEY=astraverify-admin-2024

# Enhanced security deployment
./deploy_enhanced_security.sh
```

### **Logs**
```bash
# Recent logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=astraverify-backend-staging" --limit=10 --format="table(timestamp,textPayload)"

# Current revision logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=astraverify-backend-staging AND resource.labels.revision_name=astraverify-backend-staging-00025-2nj" --limit=5 --format="table(timestamp,textPayload)"
```

### **Testing**
```bash
# Test enhanced security
node test_enhanced_security.js

# Comprehensive testing
./run_stage_tests.sh

# Quick validation
curl -s "https://astraverify-backend-staging-1098627686587.us-central1.run.app/api/check?domain=google.com" | jq '.domain'
```

---

## 🔒 **Security Testing**

### **Input Validation Test**
```bash
# Test IP rejection
curl -s -w "%{http_code}" "https://astraverify-backend-staging-1098627686587.us-central1.run.app/api/check?domain=192.168.1.1"
# Expected: 400

# Test XSS rejection
curl -s -w "%{http_code}" "https://astraverify-backend-staging-1098627686587.us-central1.run.app/api/check?domain=<script>alert('xss')</script>"
# Expected: 400
```

### **Admin Dashboard**
```bash
# Check security dashboard
curl -s -H "X-Admin-API-Key: astraverify-admin-2024" "https://astraverify-backend-staging-1098627686587.us-central1.run.app/api/admin/security-dashboard" | jq '.'

# Check blocked IPs
curl -s -H "X-Admin-API-Key: astraverify-admin-2024" "https://astraverify-backend-staging-1098627686587.us-central1.run.app/api/admin/blocked-ips" | jq '.'
```

---

## 📊 **Key Information**

### **Service URLs**
- **Backend**: `https://astraverify-backend-staging-1098627686587.us-central1.run.app`
- **Frontend**: `https://astraverify-frontend-staging-ml2mhibdvq-uc.a.run.app`
- **Current Revision**: `astraverify-backend-staging-00025-2nj`

### **Admin Credentials**
- **API Key**: `astraverify-admin-2024`
- **Header**: `X-Admin-API-Key: astraverify-admin-2024`

### **Rate Limits**
- **Free**: 10/min, 100/hour, 1,000/day
- **Authenticated**: 30/min, 500/hour, 5,000/day
- **Premium**: 100/min, 2,000/hour, 20,000/day

---

## 🔧 **Troubleshooting**

### **Common Issues**

| Issue | Command | Expected Result |
|-------|---------|----------------|
| Service down | `curl -I /api/health` | 200 OK |
| Missing headers | `curl -I /api/health \| grep X-Content-Type-Options` | Header present |
| Input validation | `curl -w "%{http_code}" "/api/check?domain=192.168.1.1"` | 400 |
| Admin access | `curl -H "X-Admin-API-Key: astraverify-admin-2024" /api/admin/security-dashboard` | JSON response |

### **Quick Fixes**

```bash
# Rollback to backup
cp backup/local_20250819_081222/app_with_security.py backend/
cp backup/local_20250819_081222/requirements.txt backend/

# Check file integrity
grep -n "X-Content-Type-Options" backend/app_with_security.py
grep -n "validate_domain" backend/app_with_security.py
grep -n "app.run" backend/app_with_security.py
```

---

## 📞 **Emergency Contacts**

- **Security**: security@astraverify.com
- **DevOps**: devops@astraverify.com
- **Dev**: dev@astraverify.com
- **Slack**: #astraverify-admin

---

## ✅ **Daily Checklist**

- [ ] Service health check
- [ ] Security headers present
- [ ] Input validation working
- [ ] Admin dashboard accessible
- [ ] No critical errors in logs
- [ ] Rate limiting functional

---

**Quick Reference v2.0** | **STAGE Environment** | **Enhanced Security**
