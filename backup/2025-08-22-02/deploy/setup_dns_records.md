# DNS Setup for AstraVerify.com

## Current Service URLs
- **Frontend**: https://astraverify-frontend-ml2mhibdvq-uc.a.run.app
- **Backend**: https://astraverify-backend-ml2mhibdvq-uc.a.run.app

## DNS Configuration

### Option 1: CNAME Records (Recommended)

Add these CNAME records to your DNS provider:

```
astraverify.com → astraverify-frontend-ml2mhibdvq-uc.a.run.app
api.astraverify.com → astraverify-backend-ml2mhibdvq-uc.a.run.app
```

### Option 2: A Records with Load Balancer

If you prefer A records, you'll need to set up a Google Cloud Load Balancer:

1. Create a load balancer pointing to your Cloud Run services
2. Use the load balancer IP for A records

## Steps to Configure

1. **Log into your DNS provider** (where you purchased astraverify.com)
2. **Add CNAME records** as shown above
3. **Wait for DNS propagation** (usually 15 minutes to 24 hours)
4. **Test the domains**:
   - https://astraverify.com
   - https://api.astraverify.com

## Testing

Once DNS is configured, test with:

```bash
curl -I https://astraverify.com
curl -I https://api.astraverify.com
```

## SSL Certificates

Google Cloud Run automatically provides SSL certificates for custom domains once DNS is properly configured. 