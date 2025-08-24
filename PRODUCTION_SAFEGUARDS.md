# AstraVerify Production Safeguards

## Overview

This document outlines the safeguards implemented to ensure that production never gets incorrect configuration and that all deployments are safe and validated.

## 🛡️ Production Safeguards

### 1. Pre-commit Hook Validation

**File**: `.git/hooks/pre-commit`

**Purpose**: Automatically validates configuration before any commit to main branch.

**Validations**:
- ✅ Ensures `App.js` imports from `./config` not `./config.local`
- ✅ Ensures backend Dockerfile uses `app_with_security.py` not `app_enhanced_dkim.py`
- ✅ Validates all required configuration files exist
- ✅ Prevents commits that would break production

**How it works**:
```bash
# Automatically runs on every commit to main branch
git commit -m "Your commit message"
# Pre-commit hook validates configuration
# Commit only proceeds if validation passes
```

### 2. Production Deployment Validation

**File**: `deploy/validate-production-deployment.sh`

**Purpose**: Comprehensive validation before any production deployment.

**Validations**:
- ✅ Git status (main branch, clean working directory, up to date)
- ✅ Environment variables (gcloud auth, correct project)
- ✅ Frontend configuration (correct imports, app names)
- ✅ Backend configuration (correct Dockerfile, endpoints)
- ✅ Pre-deployment tests (frontend build)

**Usage**:
```bash
# Run validation manually
./deploy/validate-production-deployment.sh

# Or automatically runs before production deployment
./deploy/deploy_production.sh
```

### 3. Enhanced Production Deployment Script

**File**: `deploy/deploy_production.sh`

**Purpose**: Safe production deployment with built-in validation.

**Features**:
- ✅ Automatic validation before deployment
- ✅ Main branch requirement
- ✅ User confirmation prompt
- ✅ Proper error handling
- ✅ Deployment tagging

**Usage**:
```bash
./deploy/deploy_production.sh
```

## 🔧 Configuration Management

### Environment-Specific Configurations

| Environment | Config File | App Name | Backend URL |
|-------------|-------------|----------|-------------|
| **Local** | `frontend/src/config.local.js` | `AstraVerify (Local)` | `http://localhost:8080` |
| **Staging** | `frontend/src/config.staging.js` | `AstraVerify (Staging)` | `https://astraverify-backend-staging-*.run.app` |
| **Production** | `frontend/src/config.production.js` | `AstraVerify` | `https://astraverify-backend-ml2mhibdvq-uc.a.run.app` |

### Configuration Switching

Use the config switcher to ensure correct configuration:

```bash
# Switch to production config
./switch_config.sh production

# Switch to staging config
./switch_config.sh staging

# Switch to local config
./switch_config.sh local

# Check current config
./switch_config.sh status
```

## 🚨 Critical Configuration Rules

### Frontend Configuration

1. **App.js Import**: Must import from `./config` not `./config.local`
   ```javascript
   // ✅ CORRECT
   import config from './config';
   
   // ❌ WRONG - Will break production
   import config from './config.local';
   ```

2. **Production App Name**: Must be `AstraVerify` without `(Local)` or `(Staging)`
   ```javascript
   // ✅ CORRECT
   APP_NAME: 'AstraVerify'
   
   // ❌ WRONG
   APP_NAME: 'AstraVerify (Local)'
   ```

### Backend Configuration

1. **Dockerfile CMD**: Must use `app_with_security.py` not `app_enhanced_dkim.py`
   ```dockerfile
   # ✅ CORRECT
   CMD ["python", "app_with_security.py"]
   
   # ❌ WRONG - Will break statistics
   CMD ["python", "app_enhanced_dkim.py"]
   ```

2. **Statistics Endpoint**: Must exist in `app_with_security.py`
   ```python
   # ✅ REQUIRED
   @app.route('/api/public/statistics', methods=['GET'])
   def get_public_statistics():
       # Implementation
   ```

## 📋 Deployment Checklist

### Before Production Deployment

- [ ] Run validation: `./deploy/validate-production-deployment.sh`
- [ ] Ensure on main branch: `git branch --show-current`
- [ ] Ensure clean working directory: `git status`
- [ ] Ensure up to date: `git pull origin main`
- [ ] Set correct config: `./switch_config.sh production`
- [ ] Test frontend build: `cd frontend && npm run build`
- [ ] Verify gcloud auth: `gcloud auth list`
- [ ] Verify project: `gcloud config get-value project`

### Production Deployment Process

1. **Validation**: Automatic validation runs
2. **Confirmation**: User must type 'yes' to confirm
3. **Deployment**: Backend and frontend deployed
4. **Tagging**: Automatic git tag created
5. **Verification**: Post-deployment checks

## 🔍 Monitoring and Alerts

### Health Checks

Monitor production health:

```bash
# Check frontend
curl -s "https://astraverify.com" | grep -i "astraverify"

# Check backend
curl -s "https://astraverify-backend-ml2mhibdvq-uc.a.run.app/api/health"

# Check statistics
curl -s "https://astraverify-backend-ml2mhibdvq-uc.a.run.app/api/public/statistics"
```

### Log Monitoring

Monitor deployment logs:

```bash
# Backend logs
gcloud run services logs read astraverify-backend --region=us-central1 --limit=50

# Frontend logs
gcloud run services logs read astraverify-frontend --region=us-central1 --limit=50
```

## 🚨 Emergency Procedures

### If Production Configuration is Incorrect

1. **Immediate Fix**:
   ```bash
   # Switch to correct config
   ./switch_config.sh production
   
   # Rebuild and redeploy
   ./deploy/deploy_production.sh
   ```

2. **Rollback** (if needed):
   ```bash
   # Rollback to previous version
   git log --oneline -5  # Find previous good commit
   git checkout <previous-commit-hash>
   ./deploy/deploy_production.sh
   ```

### If Validation Fails

1. **Check the error message** from validation script
2. **Fix the specific issue** (wrong import, wrong Dockerfile, etc.)
3. **Re-run validation**: `./deploy/validate-production-deployment.sh`
4. **Proceed with deployment** only after validation passes

## 📚 Best Practices

### Development Workflow

1. **Always develop on feature branches**
2. **Test changes locally** before committing
3. **Use staging environment** for testing
4. **Only merge to main** after thorough testing
5. **Always run validation** before production deployment

### Configuration Management

1. **Never commit local config** to main branch
2. **Always use environment-specific configs**
3. **Test configuration switching** before deployment
4. **Verify configuration** after deployment

### Deployment Safety

1. **Always validate** before production deployment
2. **Use deployment scripts** instead of manual commands
3. **Monitor deployments** and verify success
4. **Keep deployment tags** for tracking and rollback

## 🎯 Summary

These safeguards ensure that:

- ✅ **Production never gets incorrect configuration**
- ✅ **All deployments are validated and safe**
- ✅ **Configuration errors are caught early**
- ✅ **Rollback procedures are available**
- ✅ **Deployment process is documented and repeatable**

By following these safeguards and procedures, AstraVerify production environment will remain stable and correctly configured at all times.
