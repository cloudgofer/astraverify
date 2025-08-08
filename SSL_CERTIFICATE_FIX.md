# SSL Certificate Fix for Custom Domains

## Issue Identified
You're seeing "Your connection is not private" errors when accessing:
- `https://astraverify.com`
- `https://api.astraverify.com`

## Root Cause
The custom domains were configured in Cloud Run but the DNS records were not properly set up, preventing SSL certificate provisioning.

## DNS Records Required

### For `astraverify.com` (Frontend)
Add these A and AAAA records to your DNS provider:

```
Type: A
Name: astraverify-frontend
Value: 216.239.32.21

Type: A
Name: astraverify-frontend
Value: 216.239.34.21

Type: A
Name: astraverify-frontend
Value: 216.239.36.21

Type: A
Name: astraverify-frontend
Value: 216.239.38.21

Type: AAAA
Name: astraverify-frontend
Value: 2001:4860:4802:32::15

Type: AAAA
Name: astraverify-frontend
Value: 2001:4860:4802:34::15

Type: AAAA
Name: astraverify-frontend
Value: 2001:4860:4802:36::15

Type: AAAA
Name: astraverify-frontend
Value: 2001:4860:4802:38::15
```

### For `api.astraverify.com` (Backend)
Add this CNAME record to your DNS provider:

```
Type: CNAME
Name: api
Value: ghs.googlehosted.com.
```

## Steps to Fix

### 1. Configure DNS Records
1. Log into your DNS provider (where astraverify.com is registered)
2. Add the DNS records listed above
3. Wait for DNS propagation (can take up to 48 hours, usually 15-30 minutes)

### 2. Verify DNS Configuration
After adding the records, test with:
```bash
nslookup astraverify.com
nslookup api.astraverify.com
```

### 3. Monitor Certificate Provisioning
The SSL certificates will be automatically provisioned once DNS is properly configured:
```bash
gcloud beta run domain-mappings describe --domain=astraverify.com --region=us-central1
gcloud beta run domain-mappings describe --domain=api.astraverify.com --region=us-central1
```

### 4. Test SSL Connection
Once DNS is propagated and certificates are provisioned:
```bash
curl -I https://astraverify.com
curl -I https://api.astraverify.com
```

## Current Status
- ✅ Domain mappings recreated in Cloud Run
- ⏳ Waiting for DNS configuration
- ⏳ Waiting for SSL certificate provisioning

## Alternative Solution
If you prefer to use the Cloud Run URLs directly (which work immediately):
- **Frontend**: https://astraverify-frontend-ml2mhibdvq-uc.a.run.app
- **Backend**: https://astraverify-backend-ml2mhibdvq-uc.a.run.app

These URLs have valid SSL certificates and work immediately without custom domain configuration.
