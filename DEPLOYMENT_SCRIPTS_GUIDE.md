# Deployment Scripts Guide

## Environment-Specific Deployment Scripts

This guide outlines the proper deployment scripts for each environment. **Always use environment-specific deployment scripts** to ensure proper configuration and safety measures.

## 🏭 Production Environment

### Script: `deploy/deploy_production.sh`
**Purpose**: Deploy to production environment with full safety measures

**Features**:
- ✅ **Branch Validation**: Only allows deployment from `main` branch
- ✅ **Safety Confirmation**: Requires explicit "yes" confirmation
- ✅ **Production Resources**: 1Gi RAM, 2 CPU, 20 max instances
- ✅ **Environment Variables**: Sets `ENVIRONMENT=production`
- ✅ **Auto Config Generation**: Creates `config.production.js` dynamically
- ✅ **Deployment Tagging**: Creates git tags for tracking
- ✅ **Enhanced APIs**: Enables Firestore and Secret Manager APIs

**Usage**:
```bash
./deploy/deploy_production.sh
```

**Requirements**:
- Must be on `main` branch
- Must confirm with "yes"
- Must be authenticated with gcloud

---

## 🧪 Staging Environment

### Script: `deploy/deploy_staging.sh`
**Purpose**: Deploy to staging environment for testing

**Features**:
- ✅ **Staging Resources**: 512Mi RAM, 1 CPU, 10 max instances
- ✅ **Environment Variables**: Sets `ENVIRONMENT=staging`
- ✅ **Staging Services**: Uses `astraverify-backend-staging` and `astraverify-frontend-staging`
- ✅ **No Branch Restrictions**: Can deploy from any branch
- ✅ **Auto Config Generation**: Creates `config.staging.js` dynamically

**Usage**:
```bash
./deploy/deploy_staging.sh
```

**Requirements**:
- Must be authenticated with gcloud
- No branch restrictions

---

## 💻 Local Development

### Script: `deploy/deploy_local.sh`
**Purpose**: Set up local development environment

**Features**:
- ✅ **Local Services**: Runs frontend and backend locally
- ✅ **Dependencies**: Installs Node.js and Python dependencies
- ✅ **Config Creation**: Creates `config.local.js` automatically
- ✅ **Virtual Environment**: Sets up Python virtual environment
- ✅ **No Cloud Deployment**: Everything runs locally

**Usage**:
```bash
./deploy/deploy_local.sh
```

**Requirements**:
- Node.js installed
- Python 3 installed
- npm installed

---

## 🔧 Utility Scripts

### Frontend-Only Deployment
- **Script**: `deploy/deploy_frontend_cloudrun.sh`
- **Purpose**: Deploy only frontend to Cloud Run
- **Usage**: `./deploy/deploy_frontend_cloudrun.sh`

### Frontend to Google Cloud Storage
- **Script**: `deploy/deploy_frontend_gcs.sh`
- **Purpose**: Deploy frontend to Google Cloud Storage
- **Usage**: `./deploy/deploy_frontend_gcs.sh`

### Full Deployment with Validation
- **Script**: `deploy/deploy_with_validation.sh`
- **Purpose**: Deploy to multiple environments with validation
- **Usage**: `./deploy/deploy_with_validation.sh`

### Sync Production with Staging
- **Script**: `deploy/sync_prod_with_stage.sh`
- **Purpose**: Sync production environment with staging
- **Usage**: `./deploy/sync_prod_with_stage.sh`

### Environment Status Check
- **Script**: `deploy/check_environment_status.sh`
- **Purpose**: Check status of all environments
- **Usage**: `./deploy/check_environment_status.sh`

---

## 🚫 Removed Scripts

### `deploy_to_gcp.sh` (DELETED)
**Reason for Removal**:
- ❌ Generic script without environment-specific configurations
- ❌ No safety measures for production
- ❌ No branch validation
- ❌ Could cause confusion and deployment errors
- ❌ Redundant with environment-specific scripts

**Replacement**: Use `deploy_production.sh` or `deploy_staging.sh` instead

---

## 📋 Best Practices

1. **Always use environment-specific scripts** for deployments
2. **Never use generic deployment scripts** that don't specify environment
3. **Verify you're on the correct branch** before production deployment
4. **Confirm deployment** when prompted for production
5. **Check environment status** before and after deployment
6. **Use staging first** to test changes before production

---

## 🔄 Deployment Workflow

### For New Features:
1. Develop on feature branch
2. Test locally: `./deploy/deploy_local.sh`
3. Deploy to staging: `./deploy/deploy_staging.sh`
4. Test in staging environment
5. Merge to main branch
6. Deploy to production: `./deploy/deploy_production.sh`

### For Hotfixes:
1. Create hotfix branch from main
2. Make changes
3. Test locally: `./deploy/deploy_local.sh`
4. Merge to main
5. Deploy to production: `./deploy/deploy_production.sh`

---

## 🆘 Troubleshooting

### Common Issues:
- **Wrong branch**: Ensure you're on `main` for production
- **Authentication**: Run `gcloud auth login` if not authenticated
- **API not enabled**: Scripts will enable required APIs automatically
- **Build failures**: Check logs for dependency or configuration issues

### Environment Status:
```bash
./deploy/check_environment_status.sh
```

### Fix Frontend Issues:
```bash
./deploy/fix_frontend.sh
```
