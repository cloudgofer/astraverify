# AstraVerify Deployment Prevention Guide

## Overview

This guide outlines comprehensive measures to prevent configuration mismatches and deployment issues across all environments (LOCAL, STAGING, and PRODUCTION). These measures ensure that the "Failed to fetch" error and similar issues never occur again.

## 🛡️ Prevention Layers

### 1. Pre-Commit Validation (Git Hooks)

**File**: `.git/hooks/pre-commit`

**Purpose**: Validates configuration files before any commit is made.

**What it checks**:
- Configuration file existence and structure
- API URL consistency for each environment
- Prevention of configuration mismatches
- Detection of hardcoded URLs
- Sensitive information detection

**Usage**: Automatically runs on every commit
```bash
# The hook runs automatically, but you can test it manually:
.git/hooks/pre-commit
```

### 2. Pre-Deployment Validation

**File**: `deploy/validate-deployment-prerequisites.sh`

**Purpose**: Comprehensive validation before deployment to any environment.

**What it validates**:
- Environment-specific configuration
- Service accessibility
- Dependencies installation
- Git status and branch validation
- Google Cloud authentication

**Usage**:
```bash
# Validate specific environment
./deploy/validate-deployment-prerequisites.sh local
./deploy/validate-deployment-prerequisites.sh staging
./deploy/validate-deployment-prerequisites.sh production

# Validate without deploying
./deploy/deploy_with_validation.sh production --validate-only
```

### 3. Enhanced Deployment Script

**File**: `deploy/deploy_with_validation.sh`

**Purpose**: Automated deployment with built-in validation and post-deployment checks.

**Features**:
- Pre-deployment validation
- Environment-specific configuration switching
- Post-deployment health checks
- Automatic rollback on failure
- Deployment tagging

**Usage**:
```bash
# Deploy to specific environment
./deploy/deploy_with_validation.sh local
./deploy/deploy_with_validation.sh staging
./deploy/deploy_with_validation.sh production

# Validate only
./deploy/deploy_with_validation.sh production --validate-only
```

### 4. CI/CD Pipeline (GitHub Actions)

**File**: `.github/workflows/deploy.yml`

**Purpose**: Automated deployment pipeline with comprehensive testing.

**Features**:
- Configuration validation
- Build and test automation
- Environment-specific deployments
- Post-deployment health checks
- Automatic tagging

**Triggers**:
- Push to `main` → Production deployment
- Push to `develop` → Staging deployment
- Pull requests → Validation only
- Manual workflow dispatch

### 5. Continuous Monitoring

**File**: `scripts/monitor-environments.sh`

**Purpose**: Continuous health monitoring of all environments.

**Features**:
- Service health checks
- API functionality testing
- Configuration consistency validation
- Continuous monitoring mode
- Health report generation

**Usage**:
```bash
# Single health check
./scripts/monitor-environments.sh

# Check specific environment
./scripts/monitor-environments.sh production

# Continuous monitoring
./scripts/monitor-environments.sh --continuous 300

# Generate health report
./scripts/monitor-environments.sh --report
```

## 🔧 Configuration Management

### Environment-Specific Configurations

**Local Development** (`frontend/src/config.js`):
```javascript
const config = {
  API_BASE_URL: 'http://localhost:8080',
  APP_NAME: 'AstraVerify (Local)',
  APP_DESCRIPTION: 'Email Domain Verification Tool - Local Development'
};
```

**Staging** (`frontend/src/config.staging.js`):
```javascript
const config = {
  API_BASE_URL: 'https://astraverify-backend-staging-ml2mhibdvq-uc.a.run.app',
  APP_NAME: 'AstraVerify (Staging)',
  APP_DESCRIPTION: 'Email Domain Verification Tool - Staging'
};
```

**Production** (`frontend/src/config.production.js`):
```javascript
const config = {
  API_BASE_URL: 'https://astraverify-backend-ml2mhibdvq-uc.a.run.app',
  APP_NAME: 'AstraVerify',
  APP_DESCRIPTION: 'Email Domain Verification Tool'
};
```

### Configuration Validation Rules

1. **Local Config**: Must point to `localhost:8080`
2. **Staging Config**: Must point to staging backend URL
3. **Production Config**: Must point to production backend URL
4. **No Cross-Environment References**: Each config must only reference its own environment

## 🚀 Deployment Workflows

### Local Development
```bash
# Start local environment with validation
./deploy/deploy_with_validation.sh local

# Validate local setup
./deploy/validate-deployment-prerequisites.sh local
```

### Staging Deployment
```bash
# Deploy to staging with full validation
./deploy/deploy_with_validation.sh staging

# Or use GitHub Actions (automatic on develop branch)
git push origin develop
```

### Production Deployment
```bash
# Deploy to production with confirmation
./deploy/deploy_with_validation.sh production

# Or use GitHub Actions (automatic on main branch)
git push origin main
```

## 📊 Monitoring and Alerting

### Health Check Endpoints

**Backend Health**: `{backend_url}/api/check?domain=example.com`
**Frontend Health**: `{frontend_url}/`
**Domain Analysis**: `{backend_url}/api/check?domain=google.com&progressive=true`

### Monitoring Commands

```bash
# Quick health check
./scripts/monitor-environments.sh

# Continuous monitoring (every 5 minutes)
./scripts/monitor-environments.sh --continuous 300

# Generate detailed report
./scripts/monitor-environments.sh --report
```

### Alert Conditions

- Service unresponsive for 3 consecutive checks
- Configuration mismatch detected
- API functionality failure
- Domain analysis failure

## 🔍 Troubleshooting

### Common Issues and Solutions

#### 1. Configuration Mismatch
**Symptoms**: "Failed to fetch" error
**Solution**: 
```bash
# Validate configuration
./deploy/validate-deployment-prerequisites.sh production

# Fix configuration
cp frontend/src/config.production.js frontend/src/config.js
```

#### 2. Service Unavailable
**Symptoms**: Health checks failing
**Solution**:
```bash
# Check service status
./scripts/monitor-environments.sh production

# Redeploy if needed
./deploy/deploy_with_validation.sh production
```

#### 3. Pre-commit Hook Failing
**Symptoms**: Git commit rejected
**Solution**:
```bash
# Check what's wrong
.git/hooks/pre-commit

# Fix configuration issues
# Re-commit
```

## 📋 Best Practices

### 1. Always Use Validation
- Never deploy without running validation first
- Use `--validate-only` flag to test without deploying

### 2. Environment Isolation
- Never mix configurations between environments
- Always use environment-specific config files

### 3. Git Workflow
- Work on feature branches
- Merge to `develop` for staging deployment
- Merge to `main` for production deployment

### 4. Monitoring
- Set up continuous monitoring for production
- Generate regular health reports
- Respond to alerts immediately

### 5. Testing
- Test in local environment first
- Validate in staging before production
- Use automated tests in CI/CD pipeline

## 🛠️ Maintenance

### Regular Tasks

1. **Weekly**: Run health reports for all environments
2. **Monthly**: Review and update validation rules
3. **Quarterly**: Update deployment scripts and monitoring

### Script Maintenance

```bash
# Update script permissions
chmod +x deploy/*.sh
chmod +x scripts/*.sh
chmod +x .git/hooks/pre-commit

# Test validation scripts
./deploy/validate-deployment-prerequisites.sh local
./deploy/validate-deployment-prerequisites.sh staging
./deploy/validate-deployment-prerequisites.sh production
```

## 📞 Emergency Procedures

### Production Issues

1. **Immediate Response**:
   ```bash
   # Check production health
   ./scripts/monitor-environments.sh production
   
   # Generate health report
   ./scripts/monitor-environments.sh --report
   ```

2. **Quick Fix**:
   ```bash
   # Redeploy with validation
   ./deploy/deploy_with_validation.sh production
   ```

3. **Rollback** (if needed):
   ```bash
   # Deploy previous version
   git checkout <previous-tag>
   ./deploy/deploy_with_validation.sh production
   ```

### Contact Information

- **Primary Contact**: DevOps Team
- **Backup Contact**: Development Team
- **Emergency**: Use GitHub Issues for tracking

## 📈 Success Metrics

### Prevention Metrics

- **Configuration Errors**: 0 (target)
- **Deployment Failures**: <1% (target)
- **Service Downtime**: <5 minutes (target)
- **Recovery Time**: <10 minutes (target)

### Monitoring Metrics

- **Health Check Success Rate**: >99.9%
- **Response Time**: <2 seconds
- **Uptime**: >99.9%

---

## 🎯 Summary

This comprehensive prevention system ensures:

1. **No Configuration Mismatches**: Multiple validation layers prevent wrong configurations
2. **Automated Validation**: Pre-commit hooks and CI/CD prevent bad deployments
3. **Continuous Monitoring**: Real-time health checks catch issues early
4. **Quick Recovery**: Automated deployment scripts enable fast fixes
5. **Documentation**: Clear procedures for all scenarios

By following these guidelines and using the provided tools, the "Failed to fetch" error and similar issues will be prevented across all environments.
