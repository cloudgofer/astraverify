# AstraVerify Deployment Guide

## Quick Reference

### Environment Overview

| Environment | Branch | Script | Purpose | URL |
|-------------|--------|--------|---------|-----|
| **LOCAL** | Any branch | `./deploy/deploy_local.sh` | Development & Testing | http://localhost:3000 |
| **STAGING** | `release/YYYY-MM` | `./deploy/deploy_staging.sh` | Pre-production Testing | GCP Cloud Run |
| **PRODUCTION** | `main` only | `./deploy/deploy_production.sh` | Live Production | GCP Cloud Run |

## Deployment Commands

### Local Development
```bash
# Setup local environment
./deploy/deploy_local.sh

# Start both services
./run_local.sh
```

### Staging Deployment
```bash
# Deploy to staging (from release branch)
git checkout release/2025-08
./deploy/deploy_staging.sh
```

### Production Deployment
```bash
# Deploy to production (from main branch only)
git checkout main
./deploy/deploy_production.sh
```

## Monthly Release Workflow

### 1. Development Phase (Ongoing)
```bash
# Create feature branch
git checkout develop
git checkout -b feature/new-feature

# Develop and test locally
./deploy/deploy_local.sh
./run_local.sh

# Merge to develop when ready
git checkout develop
git merge feature/new-feature
git push origin develop
```

### 2. Stabilization Phase (1-2 weeks before release)
```bash
# Create release branch
git checkout develop
git checkout -b release/2025-08
git push -u origin release/2025-08

# Deploy to staging
./deploy/deploy_staging.sh

# Test and fix bugs (no new features)
# ... testing and bug fixes ...

# Update release branch
git add .
git commit -m "fix: resolve staging issues"
git push origin release/2025-08
```

### 3. Production Release (End of month)
```bash
# Merge to main
git checkout main
git merge release/2025-08
git push origin main

# Deploy to production
./deploy/deploy_production.sh

# Tag the release
git tag v2025.8.0
git push origin v2025.8.0

# Clean up
git branch -d release/2025-08
git push origin --delete release/2025-08
```

## Environment-Specific Configurations

### Local Environment
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8080
- **Database**: Local Firestore emulator (if needed)
- **Configuration**: `frontend/src/config.local.js`

### Staging Environment
- **Services**: `astraverify-frontend-staging`, `astraverify-backend-staging`
- **Resources**: 512Mi RAM, 1 CPU (backend), 256Mi RAM, 0.5 CPU (frontend)
- **Configuration**: `frontend/src/config.staging.js`
- **Environment Variable**: `ENVIRONMENT=staging`

### Production Environment
- **Services**: `astraverify-frontend`, `astraverify-backend`
- **Resources**: 1Gi RAM, 2 CPU (backend), 512Mi RAM, 1 CPU (frontend)
- **Configuration**: `frontend/src/config.production.js`
- **Environment Variable**: `ENVIRONMENT=production`
- **Safety**: Confirmation prompt required

## Branch Protection Rules

### Main Branch (Production)
- ✅ Requires pull request reviews
- ✅ Requires status checks to pass
- ❌ No direct pushes
- ✅ Requires up-to-date branches

### Develop Branch (Development)
- ✅ Requires pull request reviews
- ✅ Requires status checks to pass
- ❌ No direct pushes

### Release Branches (Staging)
- ✅ Requires pull request reviews
- ✅ Requires status checks to pass
- ❌ No direct pushes

## Troubleshooting

### Common Issues

#### 1. Production Deployment Blocked
```bash
# Error: Production deployment can only be done from main branch!
# Solution: Checkout main branch first
git checkout main
./deploy/deploy_production.sh
```

#### 2. Staging Deployment Issues
```bash
# Error: Backend build failed
# Solution: Check backend code and dependencies
cd backend
pip install -r requirements.txt
```

#### 3. Local Development Issues
```bash
# Error: Frontend build failed
# Solution: Check frontend dependencies
cd frontend
npm install
npm run build
```

### Environment Variables

#### Required for All Environments
- `ENVIRONMENT`: Set to `local`, `staging`, or `production`

#### Required for Staging/Production
- `EMAIL_PASSWORD`: Email service password
- `ADMIN_API_KEY`: Admin authentication key

### Logs and Monitoring

#### Local
- Frontend logs: Browser console
- Backend logs: Terminal output

#### Staging/Production
```bash
# View logs
./logs.sh

# Tail logs in real-time
./tail_logs.sh
```

## Best Practices

### 1. Always Test Locally First
```bash
./deploy/deploy_local.sh
./run_local.sh
# Test thoroughly before staging
```

### 2. Use Feature Branches
```bash
# Never work directly on develop or main
git checkout -b feature/your-feature
# Develop, test, then merge
```

### 3. Staging Before Production
```bash
# Always deploy to staging first
./deploy/deploy_staging.sh
# Test in staging environment
# Then deploy to production
```

### 4. Tag Releases
```bash
# Tag production releases
git tag v2025.8.0
git push origin v2025.8.0
```

### 5. Monitor Deployments
```bash
# Check deployment status
gcloud run services list --region=us-central1

# View service details
gcloud run services describe astraverify-backend --region=us-central1
```

## Quick Commands Reference

```bash
# Local development
./deploy/deploy_local.sh
./run_local.sh

# Staging deployment
./deploy/deploy_staging.sh

# Production deployment
./deploy/deploy_production.sh

# View logs
./logs.sh

# Tail logs
./tail_logs.sh

# Check services
gcloud run services list --region=us-central1
```
