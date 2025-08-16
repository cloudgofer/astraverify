# AstraVerify Versioning System

## Overview
AstraVerify uses a semantic versioning system with the format: `YYYYMM.DD.NN-Beta`

- **YYYYMM**: Year and month (e.g., 2025.08)
- **DD**: Day of the month (e.g., 15)
- **NN**: Daily build counter (e.g., 01, 02, 03...)
- **Beta**: Release type (Beta for development)

## Version Management

### Current Version
The current version is stored in the `VERSION` file at the root of the project.

### Version Script Usage

```bash
# Show current version
./version.sh show

# Increment version number
./version.sh increment

# Increment version and create git tag
./version.sh tag
```

### Examples

```bash
# Current version
2025.08.15.01-Beta

# After increment on same day
2025.08.15.02-Beta

# After increment on new day
2025.08.16.01-Beta
```

## Deployment with Versioning

### Local Deployment
Use the local deployment script that includes version tagging:

```bash
./deploy_local_with_version.sh
```

This script will:
1. Check for uncommitted changes
2. Increment version and create git tag
3. Update frontend version file
4. Start backend and frontend services
5. Display version information

### Manual Version Update
To manually update version:

```bash
# Increment version
./version.sh increment

# Create git tag
git add VERSION
git commit -m "Update version to $(cat VERSION)"
git tag "v$(cat VERSION)"
```

## Version Display

### Frontend
The version is displayed in the footer of the web application:
- **Footer Text**: `v2025.08.15.01-Beta | © AstraVerify.com - a CloudGofer.com service`

### Email Reports
The version is included in email report footers:
- **Email Footer**: `v2025.08.15.01-Beta | © AstraVerify.com - a CloudGofer.com service`

## Best Practices

### When to Increment Version
- **Feature additions**: Increment version
- **Bug fixes**: Increment version
- **Daily deployments**: Increment version
- **Major releases**: Consider changing release type (Beta → Release)

### Git Tags
- Each version should have a corresponding git tag
- Tag format: `vYYYYMM.DD.NN-Beta`
- Tags help track releases and enable rollbacks

### Version File Updates
- Frontend version file: `frontend/src/version.js`
- Backend reads from: `VERSION` file
- Both should be updated together

## Environment-Specific Versioning

### Local Development
- Uses local versioning system
- Version displayed in footer and emails
- Git tags created for local deployments

### Staging/Production
- Same versioning system applies
- Version displayed in all environments
- Consistent version tracking across environments

## Troubleshooting

### Version Not Updating
1. Check if `VERSION` file exists
2. Ensure version script has execute permissions
3. Verify git repository is clean

### Frontend Not Showing Version
1. Check `frontend/src/version.js` file
2. Ensure frontend is restarted after version update
3. Clear browser cache if needed

### Email Version Missing
1. Check if backend can read `VERSION` file
2. Verify backend is restarted after version update
3. Check email template includes version footer
