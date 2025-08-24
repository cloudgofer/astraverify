# 🚀 AstraVerify Quick Reference Card

## 🚨 Emergency Commands

### Production Issues
```bash
# Quick health check
./scripts/monitor-environments.sh production

# Fix configuration and redeploy
cp frontend/src/config.production.js frontend/src/config.js
./deploy/deploy_with_validation.sh production
```

### Local Development
```bash
# Start local environment
./deploy/deploy_with_validation.sh local

# Validate local setup
./deploy/validate-deployment-prerequisites.sh local
```

## 📋 Daily Commands

### Health Checks
```bash
# Check all environments
./scripts/monitor-environments.sh

# Check specific environment
./scripts/monitor-environments.sh staging

# Generate health report
./scripts/monitor-environments.sh --report
```

### Deployment
```bash
# Deploy to staging
./deploy/deploy_with_validation.sh staging

# Deploy to production
./deploy/deploy_with_validation.sh production

# Validate only (no deployment)
./deploy/deploy_with_validation.sh production --validate-only
```

## 🔧 Configuration Files

| Environment | Config File | Backend URL |
|-------------|-------------|-------------|
| **Local** | `frontend/src/config.js` | `http://localhost:8080` |
| **Staging** | `frontend/src/config.staging.js` | `https://astraverify-backend-staging-*.run.app` |
| **Production** | `frontend/src/config.production.js` | `https://astraverify-backend-ml2mhibdvq-uc.a.run.app` |

## 🛡️ Prevention Checklist

### Before Committing
- [ ] Pre-commit hook runs successfully
- [ ] Configuration files are correct for environment
- [ ] No hardcoded URLs in code

### Before Deploying
- [ ] Run validation: `./deploy/validate-deployment-prerequisites.sh <env>`
- [ ] Check git status and branch
- [ ] Ensure correct configuration is set

### After Deploying
- [ ] Run health checks: `./scripts/monitor-environments.sh <env>`
- [ ] Test domain analysis functionality
- [ ] Verify configuration consistency

## 🚨 Common Issues & Fixes

### "Failed to fetch" Error
```bash
# 1. Check configuration
grep "API_BASE_URL" frontend/src/config.js

# 2. Fix if wrong
cp frontend/src/config.production.js frontend/src/config.js

# 3. Redeploy
./deploy/deploy_with_validation.sh production
```

### Pre-commit Hook Failing
```bash
# Check what's wrong
.git/hooks/pre-commit

# Fix configuration issues
# Re-commit
```

### Service Unavailable
```bash
# Check health
./scripts/monitor-environments.sh production

# Redeploy if needed
./deploy/deploy_with_validation.sh production
```

## 📊 URLs

### Production
- **Frontend**: https://astraverify-frontend-ml2mhibdvq-uc.a.run.app
- **Backend**: https://astraverify-backend-ml2mhibdvq-uc.a.run.app

### Staging
- **Frontend**: https://astraverify-frontend-staging-ml2mhibdvq-uc.a.run.app
- **Backend**: https://astraverify-backend-staging-ml2mhibdvq-uc.a.run.app

### Local
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8080

## 🔍 Monitoring

### Continuous Monitoring
```bash
# Start continuous monitoring (every 5 minutes)
./scripts/monitor-environments.sh --continuous 300
```

### Health Check Endpoints
- **Backend**: `{backend_url}/api/check?domain=example.com`
- **Frontend**: `{frontend_url}/`
- **Domain Analysis**: `{backend_url}/api/check?domain=google.com&progressive=true`

## 📞 Emergency Contacts

- **DevOps Team**: Primary contact for deployment issues
- **Development Team**: Backup contact for technical issues
- **GitHub Issues**: For tracking and documentation

## 🎯 Success Metrics

- **Configuration Errors**: 0 (target)
- **Deployment Failures**: <1% (target)
- **Service Downtime**: <5 minutes (target)
- **Recovery Time**: <10 minutes (target)

---

**Remember**: Always validate before deploying, monitor after deploying, and use the right configuration for each environment!
