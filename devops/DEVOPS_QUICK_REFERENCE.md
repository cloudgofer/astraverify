# AstraVerify DevOps Quick Reference

## Git Branching Strategy Enforcement

### Branch Structure
- **LOCAL**: Always deploy from `develop`
- **STAGE**: Always deploy from monthly branch (e.g., `release/2025-08`)
- **PROD**: Always deploy from `main` with version tagging

### Quick Commands

#### 1. Check Current Status
```bash
./devops/enforce-branching-strategy.sh status
```

#### 2. Deploy to LOCAL Environment
```bash
./devops/enforce-branching-strategy.sh local
```
**Requirements:**
- Must be on `develop` branch
- Clean working directory
- All changes committed

#### 3. Deploy to STAGE Environment
```bash
./devops/enforce-branching-strategy.sh stage
```
**Requirements:**
- `develop` must be merged into monthly branch
- Clean working directory
- Monthly branch exists (auto-created if needed)

#### 4. Deploy to PROD Environment
```bash
./devops/enforce-branching-strategy.sh prod
```
**Requirements:**
- Must be on `main` branch
- Clean working directory
- Confirmation prompt
- Creates version tag automatically

#### 5. Validate STAGE Deployment
```bash
./devops/enforce-branching-strategy.sh validate-stage
```

#### 6. Create Production Tag Only
```bash
./devops/enforce-branching-strategy.sh create-tag
```

#### 7. Rollback to Last Production Tag
```bash
./devops/enforce-branching-strategy.sh rollback
```

## Manual Git Commands

### Feature Development Workflow
```bash
# Create feature branch
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name

# Develop and commit
git add .
git commit -m "feat: your feature description"

# Merge to develop
git checkout develop
git merge feature/your-feature-name
git push origin develop
```

### Monthly Branch Management
```bash
# Create monthly branch from develop
git checkout develop
git checkout -b release/2025-08
git push -u origin release/2025-08

# Merge develop into monthly branch
git checkout release/2025-08
git merge develop
git push origin release/2025-08
```

### Production Deployment
```bash
# Merge monthly branch to main
git checkout main
git merge release/2025-08
git push origin main

# Create version tag
./version.sh tag
git push origin v2025.08.15.01

# Deploy to production
./deploy/deploy_production.sh
```

## Version Tagging

### Tag Format
- **Format**: `vYYYY.MM.DD.NN` (e.g., `v2025.08.15.01`)
- **Example**: `v2025.08.15.01` = August 15, 2025, build #01

### Version Management
```bash
# Show current version
./version.sh show

# Increment version
./version.sh increment

# Create tag
./version.sh tag
```

## Environment-Specific Deployments

### LOCAL Environment
- **Branch**: `develop`
- **URL**: http://localhost:3000
- **Purpose**: Development and testing
- **Deployment**: `./devops/enforce-branching-strategy.sh local`

### STAGE Environment
- **Branch**: `release/YYYY-MM` (monthly)
- **URL**: GCP Cloud Run (staging)
- **Purpose**: Pre-production testing
- **Deployment**: `./devops/enforce-branching-strategy.sh stage`

### PROD Environment
- **Branch**: `main`
- **URL**: GCP Cloud Run (production)
- **Purpose**: Live production
- **Deployment**: `./devops/enforce-branching-strategy.sh prod`

## Validation Checks

### Pre-Deployment Validations
1. **Clean Working Directory**: No uncommitted changes
2. **Branch Requirements**: Correct branch for environment
3. **Merge Validation**: Required branches are merged
4. **Remote Sync**: Local and remote are in sync

### Branch Synchronization
- ✅ `develop` → `release/YYYY-MM`: Required for STAGE
- ✅ `release/YYYY-MM` → `main`: Required for PROD
- ✅ `feature/*` → `develop`: Required for LOCAL

## Rollback Procedures

### Quick Rollback
```bash
# Create rollback branch
./devops/enforce-branching-strategy.sh rollback

# Merge rollback branch to main
git checkout main
git merge hotfix/rollback-YYYYMMDD-HHMMSS
git push origin main

# Deploy from main
./devops/enforce-branching-strategy.sh prod
```

### Manual Rollback
```bash
# Find last production tag
git tag --sort=-version:refname | grep "^v[0-9]" | head -1

# Create rollback branch
git checkout -b hotfix/rollback-$(date +%Y%m%d-%H%M%S) v2025.08.15.01
git push origin hotfix/rollback-$(date +%Y%m%d-%H%M%S)
```

## Troubleshooting

### Common Issues

#### 1. "Working directory is not clean"
```bash
# Commit changes
git add .
git commit -m "feat: your changes"

# Or stash changes
git stash
```

#### 2. "develop is NOT merged into monthly branch"
```bash
# Auto-fix: Run stage deployment
./devops/enforce-branching-strategy.sh stage

# Manual fix: Merge develop into monthly branch
git checkout release/2025-08
git merge develop
git push origin release/2025-08
```

#### 3. "Production deployment can only be done from main branch"
```bash
# Switch to main branch
git checkout main
git pull origin main
./devops/enforce-branching-strategy.sh prod
```

### Emergency Procedures

#### Emergency Hotfix
```bash
# Create hotfix branch from main
git checkout main
git checkout -b hotfix/emergency-fix

# Make changes and commit
git add .
git commit -m "fix: emergency fix description"

# Create tag and deploy
./version.sh tag
./devops/enforce-branching-strategy.sh prod
```

#### Force Rollback
```bash
# Reset main to last production tag
git checkout main
git reset --hard v2025.08.15.01
git push --force origin main

# Deploy immediately
./devops/enforce-branching-strategy.sh prod
```

## Best Practices

### 1. Always Use the Enforcement Script
- Use `./devops/enforce-branching-strategy.sh` for all deployments
- Don't bypass the validation checks
- Follow the branching strategy strictly

### 2. Version Management
- Always create tags for production deployments
- Use semantic versioning
- Document version changes

### 3. Testing
- Test in LOCAL before STAGE
- Test in STAGE before PROD
- Validate all environments after deployment

### 4. Documentation
- Update deployment summaries
- Document any manual interventions
- Keep rollback procedures updated
