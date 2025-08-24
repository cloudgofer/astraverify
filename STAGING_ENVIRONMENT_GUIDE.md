# AstraVerify Staging Environment Guide

## Overview

The staging environment is a critical testing environment that mirrors production but uses isolated data stores and configurations. This guide ensures that staging remains properly isolated and uses the correct monthly branches and configurations.

## 🏗️ **Staging Environment Architecture**

### **Valid Staging Branches**
- `staging` - Main staging branch
- `release/2025-01-monthly` - Monthly release branch
- `release/2025-08` - Monthly release branch  
- `release/2025-08-13-total-analyses-fix` - Monthly release branch

### **Staging-Specific Components**

#### **Frontend Configuration**
- **File**: `frontend/src/config.staging.js`
- **Backend URL**: `https://astraverify-backend-staging-1098627686587.us-central1.run.app`
- **App Name**: `AstraVerify (Staging)`
- **Description**: `Email Domain Verification Tool - Staging Environment`

#### **Backend Configuration**
- **Environment Variable**: `ENVIRONMENT=staging`
- **Data Collections**:
  - `domain_analyses_staging` - Domain analysis results
  - `email_reports_staging` - Email report requests
  - `request_logs_staging` - Request logs

#### **Deployment Configuration**
- **Backend Image**: `gcr.io/astraverify/astraverify-backend-staging`
- **Frontend Image**: `gcr.io/astraverify/astraverify-frontend-staging`
- **Region**: `us-central1`
- **Environment**: `staging`

## 🛡️ **Staging Safeguards**

### **1. Pre-commit Validation**
- **File**: `.git/hooks/pre-commit-staging`
- **Purpose**: Validates staging configurations on staging branches
- **Checks**:
  - ✅ Staging backend URL is maintained
  - ✅ Staging app name is correct
  - ✅ Staging collections are preserved
  - ✅ Staging environment variables are set
  - ⚠️ Warns if production configs are modified

### **2. Deployment Validation**
- **File**: `deploy/validate-staging-environment.sh`
- **Purpose**: Comprehensive validation before staging deployment
- **Checks**:
  - ✅ Valid staging branch
  - ✅ Frontend staging configuration
  - ✅ Backend staging configuration
  - ✅ Deployment scripts
  - ✅ Environment variables
  - ✅ Data store isolation
  - ✅ Staging URLs
  - ✅ Safeguards in place

### **3. Automated Validation**
- **Trigger**: Before every staging deployment
- **Action**: Runs `validate-staging-environment.sh`
- **Result**: Deployment blocked if validation fails

## 📋 **Staging Deployment Process**

### **Prerequisites**
1. Ensure you're on a valid staging branch
2. Run staging validation: `./deploy/validate-staging-environment.sh`
3. Verify staging configurations are correct

### **Deployment Steps**
1. **Validate Environment**: Automatic validation runs
2. **Build Frontend**: `./frontend/build-env.sh staging`
3. **Build Backend**: Docker build with staging environment
4. **Deploy Backend**: Cloud Run deployment with `ENVIRONMENT=staging`
5. **Deploy Frontend**: Cloud Run deployment with staging config

### **Post-Deployment Verification**
1. **Frontend**: Check title shows "AstraVerify (Staging)"
2. **Backend**: Verify health endpoint shows `"environment": "staging"`
3. **Statistics**: Confirm staging data (not production)
4. **Data Store**: Verify staging collections are used

## 🔍 **Staging Validation Commands**

### **Manual Validation**
```bash
# Run comprehensive staging validation
./deploy/validate-staging-environment.sh

# Check staging branch
git branch --show-current

# Verify staging config
cat frontend/src/config.staging.js

# Check staging backend health
curl https://astraverify-backend-staging-1098627686587.us-central1.run.app/api/health

# Verify staging statistics
curl https://astraverify-backend-staging-1098627686587.us-central1.run.app/api/public/statistics
```

### **Expected Staging Statistics**
- **Total Analyses**: ~127 (staging data)
- **Unique Domains**: ~45 (staging data)
- **Average Security Score**: ~71.6 (staging data)
- **Top Provider**: Staging-specific data

## 🚨 **Common Issues and Solutions**

### **Issue: Staging Shows Production Statistics**
**Cause**: Frontend pointing to production backend
**Solution**: Update `frontend/src/config.staging.js` API_BASE_URL

### **Issue: Staging Uses Production Data**
**Cause**: Backend not setting `ENVIRONMENT=staging`
**Solution**: Verify deployment script sets correct environment variable

### **Issue: Wrong Branch for Staging**
**Cause**: Working on non-staging branch
**Solution**: Switch to valid staging branch (see list above)

### **Issue: Staging Config Missing**
**Cause**: `config.staging.js` not found or incorrect
**Solution**: Ensure staging config exists and is correct

## 📊 **Staging vs Production Comparison**

| Component | Staging | Production |
|-----------|---------|------------|
| **Branch** | `staging`, `release/*` | `main`, `production` |
| **Frontend URL** | `astraverify-frontend-staging-*` | `astraverify.com` |
| **Backend URL** | `astraverify-backend-staging-*` | `astraverify-backend-*` |
| **Data Store** | `*_staging` collections | `*` collections |
| **App Name** | `AstraVerify (Staging)` | `AstraVerify` |
| **Environment** | `staging` | `production` |

## 🔧 **Maintenance Tasks**

### **Monthly Tasks**
1. **Update Monthly Branch**: Create new monthly release branch
2. **Validate Configurations**: Run staging validation
3. **Test Deployment**: Deploy to staging and verify
4. **Update Documentation**: Update this guide if needed

### **Weekly Tasks**
1. **Check Staging Health**: Verify staging environment is healthy
2. **Review Statistics**: Ensure staging shows staging data
3. **Validate Safeguards**: Test validation scripts

### **Daily Tasks**
1. **Monitor Deployments**: Ensure staging deployments use correct configs
2. **Check Branch Usage**: Verify developers use correct branches

## 📞 **Support and Troubleshooting**

### **Validation Failures**
1. Run `./deploy/validate-staging-environment.sh` for detailed error messages
2. Check the specific validation that failed
3. Fix the configuration issue
4. Re-run validation

### **Deployment Issues**
1. Check staging branch is valid
2. Verify staging configurations
3. Run staging validation
4. Check Cloud Run logs for errors

### **Data Issues**
1. Verify backend environment variable
2. Check Firestore collection names
3. Confirm staging data isolation
4. Test with staging-specific domain

---

**Last Updated**: 2025-08-24
**Version**: 1.0
**Maintainer**: DevOps Team
