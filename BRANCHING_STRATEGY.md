# AstraVerify Git Branching Strategy

## Overview
This document outlines the Git branching strategy for AstraVerify, ensuring safe deployments, easy rollbacks, and proper version control.

## Branch Structure

### Main Branches
- **`main`** - Production-ready code, always deployable
- **`develop`** - Integration branch for features, staging deployments

### Supporting Branches
- **`feature/*`** - Individual feature development
- **`hotfix/*`** - Critical production fixes
- **`release/*`** - Release preparation branches

## Branch Protection Rules

### Main Branch
- Requires pull request reviews
- Requires status checks to pass
- No direct pushes allowed
- Auto-delete head branches

### Develop Branch
- Requires pull request reviews
- Requires status checks to pass
- Allows force pushes for emergency fixes

## Tagging Strategy

### Version Tags
- **Format**: `v{major}.{minor}.{patch}`
- **Example**: `v1.2.3`
- **When**: Every production deployment

### Deployment Tags
- **Format**: `deploy/{environment}/{date}-{time}`
- **Examples**: 
  - `deploy/prod/2025-08-11-1430`
  - `deploy/staging/2025-08-11-1000`

### Feature Tags
- **Format**: `feature/{feature-name}/{date}`
- **Example**: `feature/mobile-ui/2025-08-11`

## Deployment Workflows

### Staging Deployment (Monthly)
1. Create feature branch from `develop`
2. Develop and test features
3. Create PR to `develop`
4. Merge to `develop`
5. **Monthly**: Create PR from `develop` to `main`
6. Tag with `deploy/staging/{date}-{time}`
7. Deploy to staging environment

### Production Deployment
1. Create release branch from `develop`
2. Final testing and bug fixes
3. Create PR to `main`
4. Merge to `main`
5. Tag with version tag (e.g., `v1.2.3`)
6. Tag with deployment tag `deploy/prod/{date}-{time}`
7. Deploy to production

## Rollback Strategy

### Quick Rollback
```bash
# Find the previous deployment tag
git tag -l "deploy/prod/*" --sort=-version:refname | head -2

# Rollback to previous version
git checkout <previous-deployment-tag>
git checkout -b hotfix/rollback-$(date +%Y%m%d)
git push origin hotfix/rollback-$(date +%Y%m%d)
```

### Emergency Hotfix
```bash
# Create hotfix branch from main
git checkout main
git checkout -b hotfix/emergency-fix
# Make changes
git commit -m "Emergency fix: description"
git tag v1.2.4
git push origin hotfix/emergency-fix
git push origin v1.2.4
```

## Automated Scripts

### Pre-deployment Checklist
- [ ] All tests passing
- [ ] Code review completed
- [ ] Security scan passed
- [ ] Performance tests passed
- [ ] Documentation updated

### Post-deployment Checklist
- [ ] Health checks passing
- [ ] Monitoring alerts configured
- [ ] Rollback plan documented
- [ ] Deployment tag created

## Monthly Branch Check-in Process

### Staging Deployments
1. **Frequency**: Monthly
2. **Branch**: `develop` → `main`
3. **Tagging**: `deploy/staging/{YYYY-MM-DD}-{HHMM}`
4. **Automation**: GitHub Actions workflow

### Production Deployments
1. **Frequency**: As needed (after staging validation)
2. **Branch**: `main`
3. **Tagging**: 
   - Version tag: `v{major}.{minor}.{patch}`
   - Deployment tag: `deploy/prod/{YYYY-MM-DD}-{HHMM}`
4. **Automation**: GitHub Actions workflow

## Git Commands Reference

### Creating Feature Branches
```bash
git checkout develop
git pull origin develop
git checkout -b feature/feature-name
```

### Creating Release Branches
```bash
git checkout develop
git pull origin develop
git checkout -b release/v1.2.3
```

### Creating Hotfix Branches
```bash
git checkout main
git pull origin main
git checkout -b hotfix/critical-fix
```

### Tagging Commands
```bash
# Version tag
git tag -a v1.2.3 -m "Release version 1.2.3"
git push origin v1.2.3

# Deployment tag
git tag deploy/prod/2025-08-11-1430
git push origin deploy/prod/2025-08-11-1430
```

## GitHub Actions Workflows

### Staging Deployment Workflow
- Triggers on PR merge to `develop`
- Runs tests and security scans
- Creates staging deployment tag
- Deploys to staging environment

### Production Deployment Workflow
- Triggers on PR merge to `main`
- Runs full test suite
- Creates version and deployment tags
- Deploys to production environment
- Sends deployment notifications

## Monitoring and Alerts

### Deployment Monitoring
- Health check endpoints
- Performance metrics
- Error rate monitoring
- User experience metrics

### Rollback Triggers
- High error rate (>5%)
- Performance degradation (>20%)
- Security vulnerabilities
- User complaints

## Documentation Requirements

### Required Documentation
- API changes
- Database migrations
- Configuration changes
- Breaking changes
- New features

### Documentation Location
- README.md for general changes
- API.md for API changes
- CHANGELOG.md for version history
- DEPLOYMENT.md for deployment notes
