# AstraVerify Branching Strategy

## Overview
This document outlines the branching strategy for AstraVerify, following a monthly release cycle with proper stabilization and development workflows.

## Branch Structure

### Main Branches

#### `main` (Production)
- **Purpose**: Production-ready code
- **Source**: `release/YYYY-MM` branches
- **Protection**: Requires pull request approval
- **Deployment**: Automatic deployment to production

#### `develop` (Development)
- **Purpose**: Integration branch for ongoing development
- **Source**: Feature branches
- **Protection**: Requires pull request approval
- **Deployment**: Automatic deployment to staging

### Release Branches

#### `release/YYYY-MM` (Monthly Release)
- **Format**: `release/2025-08`, `release/2025-09`, etc.
- **Purpose**: Stabilization branch for monthly releases
- **Source**: `develop` branch
- **Target**: `main` branch
- **Lifetime**: Created 1-2 weeks before release, merged to main and deleted after release

**Examples:**
- `release/2025-08` - August 2025 release
- `release/2025-09` - September 2025 release
- `release/2025-10` - October 2025 release

### Feature Branches

#### `feature/description`
- **Format**: `feature/email-enhancements`, `feature/security-scoring`, etc.
- **Purpose**: Individual features or bug fixes
- **Source**: `develop` branch
- **Target**: `develop` branch
- **Naming**: Use descriptive names with hyphens

**Examples:**
- `feature/email-report-enhancements`
- `feature/security-score-calculation`
- `feature/mobile-responsive-improvements`
- `feature/bugfix-smtp-authentication`

## Workflow

### Monthly Release Process

1. **Release Preparation** (1-2 weeks before release)
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b release/2025-08
   git push -u origin release/2025-08
   ```

2. **Stabilization Period**
   - Only bug fixes and critical updates
   - No new features
   - Testing and validation
   - Documentation updates

3. **Release to Production**
   ```bash
   git checkout main
   git merge release/2025-08
   git push origin main
   git tag v1.0.0  # or appropriate version
   git push origin v1.0.0
   ```

4. **Cleanup**
   ```bash
   git branch -d release/2025-08
   git push origin --delete release/2025-08
   ```

### Feature Development Process

1. **Create Feature Branch**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/new-feature
   ```

2. **Development**
   - Make changes
   - Commit frequently with descriptive messages
   - Keep branch up to date with develop

3. **Complete Feature**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout feature/new-feature
   git rebase develop
   git push origin feature/new-feature
   ```

4. **Create Pull Request**
   - Target: `develop`
   - Review and approval required
   - Automated testing

### Hotfix Process

1. **Create Hotfix Branch**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b hotfix/critical-bug
   ```

2. **Fix and Test**
   - Make minimal changes
   - Test thoroughly
   - Update version if needed

3. **Deploy Hotfix**
   ```bash
   git checkout main
   git merge hotfix/critical-bug
   git push origin main
   git checkout develop
   git merge hotfix/critical-bug
   git push origin develop
   ```

## Branch Protection Rules

### Main Branch
- Requires pull request reviews
- Requires status checks to pass
- No direct pushes
- Requires up-to-date branches

### Develop Branch
- Requires pull request reviews
- Requires status checks to pass
- No direct pushes

### Release Branches
- Requires pull request reviews
- Requires status checks to pass
- No direct pushes

## Versioning Strategy

### Semantic Versioning (SemVer)
- **Format**: `MAJOR.MINOR.PATCH`
- **Examples**: `1.0.0`, `1.1.0`, `1.1.1`

### Monthly Release Versioning
- **Format**: `YYYY.MM.PATCH`
- **Examples**: `2025.8.0`, `2025.8.1`, `2025.9.0`

## Commit Message Convention

### Format
```
type(scope): description

[optional body]

[optional footer]
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Maintenance tasks

### Examples
```
feat(email): add professional sender name to emails
fix(smtp): resolve authentication issue with DreamHost
docs(readme): update deployment instructions
style(ui): improve mobile responsiveness
```

## Monthly Release Schedule

### August 2025 (Current)
- **Release Branch**: `release/2025-08`
- **Target Release Date**: End of August 2025
- **Stabilization Period**: 1-2 weeks before release

### September 2025
- **Release Branch**: `release/2025-09`
- **Target Release Date**: End of September 2025
- **Stabilization Period**: 1-2 weeks before release

### October 2025
- **Release Branch**: `release/2025-10`
- **Target Release Date**: End of October 2025
- **Stabilization Period**: 1-2 weeks before release

## Deployment Strategy

### Environment Mapping

#### LOCAL Environment
- **Purpose**: Development and testing
- **Branch**: Any branch (develop, feature branches)
- **Deployment**: Local development server
- **Script**: `./deploy/deploy_local.sh`
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8080

#### STAGING Environment
- **Purpose**: Pre-production testing and validation
- **Branch**: `release/YYYY-MM` branches only
- **Deployment**: GCP Cloud Run (staging services)
- **Script**: `./deploy/deploy_staging.sh`
- **Services**: `astraverify-frontend-staging`, `astraverify-backend-staging`
- **Configuration**: Staging-specific settings

#### PRODUCTION Environment
- **Purpose**: Live production environment
- **Branch**: `main` branch only
- **Deployment**: GCP Cloud Run (production services)
- **Script**: `./deploy/deploy_production.sh`
- **Services**: `astraverify-frontend`, `astraverify-backend`
- **Configuration**: Production settings with higher resources

### Deployment Workflow

```
LOCAL Development → STAGING Testing → PRODUCTION Release
     ↓                    ↓                    ↓
Feature Branches → Release Branches → Main Branch
     ↓                    ↓                    ↓
deploy_local.sh → deploy_staging.sh → deploy_production.sh
```

### Monthly Release Process

1. **Development Phase** (ongoing)
   - Work on feature branches
   - Test locally with `deploy_local.sh`
   - Merge to `develop` when ready

2. **Stabilization Phase** (1-2 weeks before release)
   - Create release branch: `release/2025-08`
   - Deploy to STAGING: `./deploy/deploy_staging.sh`
   - Testing and bug fixes only
   - No new features

3. **Production Release** (end of month)
   - Merge release branch to `main`
   - Deploy to PRODUCTION: `./deploy/deploy_production.sh`
   - Tag release with version
   - Clean up release branch

## Current Branch Status

- ✅ `main` - Production branch (PRODUCTION deployment)
- ✅ `develop` - Development integration branch (LOCAL deployment)
- ✅ `release/2025-08` - August 2025 stabilization branch (STAGING deployment)

## Next Steps

1. **Set up branch protection rules** in GitHub
2. **Configure automated testing** for pull requests
3. **Set up deployment pipelines** for each branch
4. **Create feature branches** for ongoing development
5. **Schedule monthly release reviews**

## Useful Commands

### View All Branches
```bash
git branch -a
```

### Switch Between Branches
```bash
git checkout main
git checkout develop
git checkout release/2025-08
```

### Create New Feature Branch
```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

### Update Branch with Latest Changes
```bash
git checkout your-branch
git pull origin develop
git rebase develop
```

### View Branch History
```bash
git log --oneline --graph --all
```
