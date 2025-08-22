# AstraVerify DevOps Branching Strategy Enforcement

## Overview

This document provides complete automation and enforcement for the Git branching and deployment strategy:

- **LOCAL**: Always deploy from `develop`
- **STAGE**: Always deploy from monthly branch (e.g., `release/2025-08`)
- **PROD**: Always deploy from `main` with version tagging

## 1. Commands and Automation Scripts

### Main Enforcement Script
```bash
./devops/enforce-branching-strategy.sh [command]
```

### Available Commands
```bash
# Check current status
./devops/enforce-branching-strategy.sh status

# Deploy to environments
./devops/enforce-branching-strategy.sh local
./devops/enforce-branching-strategy.sh stage
./devops/enforce-branching-strategy.sh prod

# Validation and utilities
./devops/enforce-branching-strategy.sh validate-stage
./devops/enforce-branching-strategy.sh create-tag
./devops/enforce-branching-strategy.sh rollback
```

### Prerequisites Validation Script
```bash
./devops/validate-deployment-prerequisites.sh [environment]
```

## 2. Validation: Develop → Monthly Branch Sync

### Automatic Validation
The enforcement script automatically validates that `develop` is merged into the monthly branch before STAGE deployment:

```bash
./devops/enforce-branching-strategy.sh stage
```

**Validation Process:**
1. Checks if monthly branch exists (creates if needed)
2. Validates `develop` is merged into monthly branch
3. Auto-merges `develop` into monthly branch if not synced
4. Proceeds with STAGE deployment

### Manual Validation
```bash
# Check if develop is merged into monthly branch
./devops/enforce-branching-strategy.sh validate-stage

# Manual merge if needed
git checkout release/2025-08
git merge develop
git push origin release/2025-08
```

### Validation Commands
```bash
# Check branch synchronization status
git merge-base --is-ancestor origin/develop origin/release/2025-08 && echo "SYNCED" || echo "NOT SYNCED"

# Show branch differences
git log --oneline origin/develop ^origin/release/2025-08
```

## 3. Production Tagging

### Automatic Tag Creation
Production deployment automatically creates version tags:

```bash
./devops/enforce-branching-strategy.sh prod
```

**Tag Format:** `vYYYY.MM.DD.NN` (e.g., `v2025.08.15.01`)

### Manual Tag Creation
```bash
# Create tag only (without deployment)
./devops/enforce-branching-strategy.sh create-tag

# Manual version management
./version.sh increment
./version.sh tag
```

### Tag Naming Logic
```bash
# Current version format: YYYY.MM.DD.NN-Beta
# Production tag format: vYYYY.MM.DD.NN

# Examples:
# VERSION file: 2025.08.15.02-Beta
# Production tag: v2025.08.15.02

# Logic:
# - Date changes: Reset counter to 01
# - Same date: Increment counter
# - Remove "-Beta" suffix for production tags
```

## 4. Rollback Automation

### Quick Rollback
```bash
# Create rollback branch from last production tag
./devops/enforce-branching-strategy.sh rollback

# Complete rollback process
git checkout main
git merge hotfix/rollback-YYYYMMDD-HHMMSS
git push origin main
./devops/enforce-branching-strategy.sh prod
```

### Manual Rollback
```bash
# Find last production tag
git tag --sort=-version:refname | grep "^v[0-9]" | head -1

# Create rollback branch
git checkout -b hotfix/rollback-$(date +%Y%m%d-%H%M%S) v2025.08.15.01
git push origin hotfix/rollback-$(date +%Y%m%d-%H%M%S)

# Force rollback (emergency)
git checkout main
git reset --hard v2025.08.15.01
git push --force origin main
./devops/enforce-branching-strategy.sh prod
```

## 5. Git Commands by Environment

### LOCAL Environment
```bash
# Prerequisites
git checkout develop
git pull origin develop

# Validation
./devops/validate-deployment-prerequisites.sh local

# Deployment
./devops/enforce-branching-strategy.sh local
```

### STAGE Environment
```bash
# Prerequisites
git checkout develop
git pull origin develop

# Validation
./devops/validate-deployment-prerequisites.sh stage

# Deployment (auto-validates develop → monthly branch sync)
./devops/enforce-branching-strategy.sh stage
```

### PROD Environment
```bash
# Prerequisites
git checkout main
git pull origin main

# Validation
./devops/validate-deployment-prerequisites.sh prod

# Deployment (auto-creates version tag)
./devops/enforce-branching-strategy.sh prod
```

## 6. Deployment Notes per Environment

### LOCAL Environment
- **Branch**: `develop`
- **URL**: http://localhost:3000
- **Purpose**: Development and testing
- **Requirements**: 
  - Clean working directory
  - On `develop` branch
  - Node.js and npm installed
- **Validation**: `./devops/validate-deployment-prerequisites.sh local`

### STAGE Environment
- **Branch**: `release/YYYY-MM` (monthly)
- **URL**: GCP Cloud Run (staging)
- **Purpose**: Pre-production testing
- **Requirements**:
  - Clean working directory
  - `develop` merged into monthly branch
  - gcloud CLI authenticated
- **Validation**: `./devops/validate-deployment-prerequisites.sh stage`

### PROD Environment
- **Branch**: `main`
- **URL**: GCP Cloud Run (production)
- **Purpose**: Live production
- **Requirements**:
  - Clean working directory
  - On `main` branch
  - Monthly branch merged into main
  - gcloud CLI authenticated
  - Confirmation prompt
- **Validation**: `./devops/validate-deployment-prerequisites.sh prod`

## 7. Complete Workflow Examples

### Feature Development → LOCAL → STAGE → PROD
```bash
# 1. Feature Development
git checkout develop
git checkout -b feature/new-feature
# ... develop and commit ...
git checkout develop
git merge feature/new-feature
git push origin develop

# 2. LOCAL Testing
./devops/enforce-branching-strategy.sh local

# 3. STAGE Deployment
./devops/enforce-branching-strategy.sh stage

# 4. PROD Deployment
./devops/enforce-branching-strategy.sh prod
```

### Emergency Hotfix
```bash
# 1. Create hotfix branch
git checkout main
git checkout -b hotfix/emergency-fix

# 2. Make changes and commit
git add .
git commit -m "fix: emergency fix description"

# 3. Deploy directly to PROD
./devops/enforce-branching-strategy.sh prod
```

### Monthly Release Process
```bash
# 1. Create monthly branch
git checkout develop
git checkout -b release/2025-08
git push -u origin release/2025-08

# 2. Deploy to STAGE
./devops/enforce-branching-strategy.sh stage

# 3. Merge to main
git checkout main
git merge release/2025-08
git push origin main

# 4. Deploy to PROD
./devops/enforce-branching-strategy.sh prod
```

## 8. Status Monitoring

### Check Current Status
```bash
./devops/enforce-branching-strategy.sh status
```

**Output includes:**
- Current branch
- Latest commits for each branch
- Current version
- Last production tag
- Branch synchronization status

### Monitor Branch Sync
```bash
# Check develop → monthly branch sync
git merge-base --is-ancestor origin/develop origin/release/2025-08 && echo "✅ SYNCED" || echo "❌ NOT SYNCED"

# Check monthly branch → main sync
git merge-base --is-ancestor origin/release/2025-08 origin/main && echo "✅ SYNCED" || echo "❌ NOT SYNCED"
```

## 9. Troubleshooting

### Common Issues and Solutions

#### "Working directory is not clean"
```bash
# Commit changes
git add .
git commit -m "feat: your changes"

# Or stash changes
git stash
```

#### "develop is NOT merged into monthly branch"
```bash
# Auto-fix: Run stage deployment
./devops/enforce-branching-strategy.sh stage

# Manual fix
git checkout release/2025-08
git merge develop
git push origin release/2025-08
```

#### "Production deployment can only be done from main branch"
```bash
# Switch to main branch
git checkout main
git pull origin main
./devops/enforce-branching-strategy.sh prod
```

#### "gcloud is not authenticated"
```bash
gcloud auth login
gcloud config set project astraverify
```

## 10. Best Practices

### Always Use Enforcement Scripts
- Use `./devops/enforce-branching-strategy.sh` for all deployments
- Don't bypass validation checks
- Follow the branching strategy strictly

### Version Management
- Always create tags for production deployments
- Use semantic versioning
- Document version changes

### Testing
- Test in LOCAL before STAGE
- Test in STAGE before PROD
- Validate all environments after deployment

### Documentation
- Update deployment summaries
- Document any manual interventions
- Keep rollback procedures updated

## Summary

This DevOps strategy provides:

1. **✅ Automated enforcement** of branching strategy
2. **✅ Automatic validation** of develop → monthly branch sync
3. **✅ Automatic tagging** for production deployments
4. **✅ Automated rollback** capabilities
5. **✅ Comprehensive validation** of prerequisites
6. **✅ Clear deployment notes** per environment

All commands are automated and enforce the policy without manual intervention, ensuring consistent and reliable deployments across all environments.
