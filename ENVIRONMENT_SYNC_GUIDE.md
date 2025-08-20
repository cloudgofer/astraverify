# Environment Sync Guide: PROD ↔ STAGE

This guide explains how to sync the PRODUCTION environment with STAGE code while maintaining environment-specific configurations.

## Overview

The AstraVerify application has two main environments:
- **STAGING**: Testing environment with staging-specific configurations
- **PRODUCTION**: Live environment with production-specific configurations

## Environment-Specific Configurations

### Backend Configurations

| Configuration | STAGING | PRODUCTION |
|---------------|---------|------------|
| **Service Name** | `astraverify-backend-staging` | `astraverify-backend` |
| **Memory** | 512Mi | 1Gi |
| **CPU** | 1 | 2 |
| **Max Instances** | 10 | 20 |
| **Environment Variable** | `ENVIRONMENT=staging` | `ENVIRONMENT=production` |
| **Email App Password** | `gsak aofx trxi jedl` | `mads ghsj bhdf jcjm` |

### Frontend Configurations

| Configuration | STAGING | PRODUCTION |
|---------------|---------|------------|
| **Service Name** | `astraverify-frontend-staging` | `astraverify-frontend` |
| **Memory** | 256Mi | 512Mi |
| **CPU** | 0.5 | 1 |
| **Max Instances** | 5 | 10 |
| **App Name** | `AstraVerify (Staging)` | `AstraVerify` |
| **Description** | `Email Domain Verification Tool - Staging Environment` | `Email Domain Verification Tool` |

## Quick Sync Commands

### 1. Check Current Environment Status
```bash
./deploy/check_environment_status.sh
```

This script will:
- Check if both STAGE and PROD environments are deployed
- Test health endpoints for both environments
- Show current git status
- Provide recommendations for next steps

### 2. Sync PROD with STAGE Code
```bash
./deploy/sync_prod_with_stage.sh
```

This script will:
- Deploy current STAGE code to PROD environment
- Maintain PROD-specific configurations (resources, branding, etc.)
- Set proper environment variables
- Create deployment tags for tracking
- Verify deployment health

## Manual Sync Process

If you prefer to sync manually, follow these steps:

### Step 1: Verify STAGE Environment
```bash
# Check staging backend
gcloud run services describe astraverify-backend-staging --region=us-central1

# Check staging frontend
gcloud run services describe astraverify-frontend-staging --region=us-central1
```

### Step 2: Deploy Backend to PROD
```bash
cd backend
gcloud builds submit --tag gcr.io/astraverify/astraverify-backend
gcloud run deploy astraverify-backend \
    --image gcr.io/astraverify/astraverify-backend \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 1Gi \
    --cpu 2 \
    --max-instances 20 \
    --set-env-vars="ENVIRONMENT=production"
```

### Step 3: Update Frontend Configuration
```bash
cd frontend

# Get the new backend URL
BACKEND_URL=$(gcloud run services describe astraverify-backend --region=us-central1 --format="value(status.url)")

# Update production config
cat > src/config.production.js << EOF
const config = {
  API_BASE_URL: '$BACKEND_URL',
  ENDPOINTS: {
    CHECK_DOMAIN: '/api/check'
  },
  APP_NAME: 'AstraVerify',
  APP_DESCRIPTION: 'Email Domain Verification Tool'
};
export default config;
EOF

# Update main config
cp src/config.production.js src/config.js
```

### Step 4: Deploy Frontend to PROD
```bash
npm install
npm run build
gcloud builds submit --tag gcr.io/astraverify/astraverify-frontend
gcloud run deploy astraverify-frontend \
    --image gcr.io/astraverify/astraverify-frontend \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --max-instances 10
```

## Environment-Specific Features

### Email Configuration
The backend automatically uses environment-specific email configurations:

- **STAGING**: Uses staging app password for testing
- **PRODUCTION**: Uses production app password for live emails
- **LOCAL**: Uses local app password for development

### Security Features
- **STAGING**: Lower rate limits, more verbose logging
- **PRODUCTION**: Higher rate limits, optimized performance, production logging

### Monitoring and Logging
- **STAGING**: Detailed logging for debugging
- **PRODUCTION**: Optimized logging for performance

## Verification Steps

After syncing, verify the deployment:

### 1. Health Checks
```bash
# Test backend health
curl -I https://astraverify-backend-ml2mhibdvq-uc.a.run.app/api/health

# Test frontend accessibility
curl -I https://astraverify-frontend-ml2mhibdvq-uc.a.run.app
```

### 2. Functional Testing
```bash
# Test domain verification
curl -X POST https://astraverify-backend-ml2mhibdvq-uc.a.run.app/api/check \
  -H "Content-Type: application/json" \
  -d '{"domain": "example.com"}'
```

### 3. Environment Verification
```bash
# Check environment variable
gcloud run services describe astraverify-backend --region=us-central1 --format="value(spec.template.spec.containers[0].env[0].value)"
```

## Rollback Process

If issues occur after sync, you can rollback:

### 1. Check Previous Deployment
```bash
# List deployment tags
git tag --list "deploy-*" | tail -5
```

### 2. Rollback to Previous Version
```bash
# Checkout previous deployment
git checkout <previous-deployment-tag>

# Re-run deployment
./deploy/deploy_production.sh
```

## Best Practices

1. **Always test in STAGE first**: Ensure all changes work in staging before syncing to production
2. **Use deployment tags**: Always create tags for tracking
3. **Monitor after sync**: Check application health and logs after deployment
4. **Maintain configurations**: Never override environment-specific settings during sync
5. **Document changes**: Keep track of what was synced and when

## Troubleshooting

### Common Issues

1. **Build Failures**: Check if all dependencies are installed
2. **Deployment Failures**: Verify GCP permissions and quotas
3. **Health Check Failures**: Check application logs for errors
4. **Configuration Issues**: Ensure environment variables are set correctly

### Debug Commands
```bash
# Check application logs
gcloud logs read --service=astraverify-backend --limit=50

# Check service status
gcloud run services list --region=us-central1

# Check build history
gcloud builds list --limit=10
```

## Support

For issues with environment syncing:
1. Check the troubleshooting section above
2. Review application logs
3. Verify GCP service status
4. Contact the development team

---

**Last Updated**: $(date +%Y-%m-%d)
**Version**: 1.0
