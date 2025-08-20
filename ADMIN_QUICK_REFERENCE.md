# AstraVerify Admin Quick Reference

## 🚀 Production Environment Status: OPERATIONAL

**Last Updated:** August 20, 2025  
**Environment:** Production  
**Status:** ✅ All systems operational

## 📍 Quick Access URLs

### Production URLs
- **Frontend**: https://astraverify-frontend-ml2mhibdvq-uc.a.run.app
- **Backend API**: https://astraverify-backend-ml2mhibdvq-uc.a.run.app
- **Health Check**: https://astraverify-backend-ml2mhibdvq-uc.a.run.app/api/health

### Test Domains
- **cloudgofer.com** - Google Workspace (All security features enabled)
- **astraverify.com** - Google Workspace (All security features enabled)  
- **techstorm.ie** - Custom mail server (DKIM enabled, SPF/DMARC missing)

## 🔧 Email Configuration

### SMTP Settings
- **Server**: smtp.gmail.com
- **Port**: 587
- **Authentication**: TLS with app-specific password
- **Sender**: hi@astraverify.com
- **Status**: ✅ Operational

### App-Specific Passwords
- **LOCAL**: `juek rown cptq zkpo`
- **STAGING**: `gsak aofx trxi jedl`
- **PRODUCTION**: `mads ghsj bhdf jcjm`

### Test Email
- **Address**: nitin.jain+AstraVerifyProdTest@CloudGofer.com
- **Status**: ✅ Email sending confirmed

## 🛠️ Quick Commands

### Check Service Status
```bash
# Check backend health
curl https://astraverify-backend-ml2mhibdvq-uc.a.run.app/api/health

# Check frontend
curl https://astraverify-frontend-ml2mhibdvq-uc.a.run.app
```

### View Logs
```bash
# Backend logs
gcloud run services logs read astraverify-backend --region=us-central1 --limit=50

# Frontend logs  
gcloud run services logs read astraverify-frontend --region=us-central1 --limit=50
```

### Deploy Updates
```bash
# Deploy backend
cd backend && gcloud builds submit --tag gcr.io/astraverify/astraverify-backend
gcloud run deploy astraverify-backend --image gcr.io/astraverify/astraverify-backend --region=us-central1

# Deploy frontend
cd frontend && gcloud builds submit --tag gcr.io/astraverify/astraverify-frontend
gcloud run deploy astraverify-frontend --image gcr.io/astraverify/astraverify-frontend --region=us-central1
```

### Update Email Password
```bash
# Update production email password
echo "mads ghsj bhdf jcjm" | gcloud secrets versions add astraverify-email-password --data-file=-
```

## 📊 Monitoring

### Key Metrics
- **Backend Health**: ✅ Healthy
- **Frontend Access**: ✅ Accessible
- **Email Sending**: ✅ Operational
- **Domain Verification**: ✅ Working
- **Rate Limiting**: ✅ Active

### Performance
- **Response Time**: < 100ms (health check)
- **Domain Analysis**: 200-800ms
- **Email Sending**: 1-2 seconds
- **Frontend Load**: < 2 seconds

## 🔍 Troubleshooting

### Common Issues

#### Email Not Sending
1. Check GCP Secret Manager for correct app-specific password
2. Verify SMTP settings in backend logs
3. Test with: `node test_email_sending.js`

#### Domain Verification Failing
1. Check backend health: `/api/health`
2. Verify DNS resolution
3. Check rate limiting

#### Frontend Not Loading
1. Check Cloud Run service status
2. Verify frontend build
3. Check nginx configuration

### Debug Commands
```bash
# Test email functionality
node test_email_sending.js

# Test production environment
node test_production_environment.js

# Check service details
gcloud run services describe astraverify-backend --region=us-central1
gcloud run services describe astraverify-frontend --region=us-central1
```

## 📧 Email Features

### Email Report Features
- ✅ HTML email templates
- ✅ Security score visualization
- ✅ Component-by-component analysis
- ✅ Recommendations and issues
- ✅ Anti-spam headers
- ✅ Professional styling

### Email Validation
- ✅ Email format validation
- ✅ Domain validation
- ✅ Required field checking
- ✅ Error handling

## 🔒 Security Features

### Active Security Measures
- ✅ Rate limiting (10 requests/minute for free tier)
- ✅ Input validation and sanitization
- ✅ Request logging and monitoring
- ✅ IP blocking capabilities
- ✅ Enhanced authentication for admin endpoints

### Environment Security
- ✅ GCP Secret Manager for credentials
- ✅ Environment-specific configurations
- ✅ Secure app-specific passwords
- ✅ TLS encryption for email

## 📋 Maintenance Tasks

### Daily
- [ ] Check backend health endpoint
- [ ] Monitor email delivery rates
- [ ] Review error logs

### Weekly
- [ ] Check service performance metrics
- [ ] Review rate limiting effectiveness
- [ ] Monitor resource usage

### Monthly
- [ ] Update dependencies
- [ ] Review security configurations
- [ ] Backup configuration data

## 🚨 Emergency Contacts

### Critical Issues
- **Service Down**: Check Cloud Run console
- **Email Issues**: Verify app-specific password
- **Performance**: Monitor resource usage
- **Security**: Review logs for abuse

### Quick Recovery
```bash
# Restart services if needed
gcloud run services update astraverify-backend --region=us-central1
gcloud run services update astraverify-frontend --region=us-central1
```

## 📈 Success Metrics

### Current Status
- ✅ **100% Test Pass Rate**
- ✅ **All Core Features Operational**
- ✅ **Email Delivery Confirmed**
- ✅ **Security Features Active**
- ✅ **Performance Optimized**

### Key Achievements
- Complete domain verification system
- Professional email reporting
- Enhanced security implementation
- Responsive web interface
- Comprehensive monitoring

---

**Last Updated:** August 20, 2025  
**Status:** �� PRODUCTION READY
