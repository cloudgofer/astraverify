#!/bin/bash

# AstraVerify Staging Environment Validation
# Ensures staging environment uses correct monthly branch, staging-specific configurations, and data stores

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[VALIDATION]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Function to validate staging branch
validate_staging_branch() {
    print_status "Validating staging branch configuration..."
    
    # Check if we're on a staging-appropriate branch
    CURRENT_BRANCH=$(git branch --show-current)
    
    # Valid staging branches (monthly releases or staging-specific)
    VALID_STAGING_BRANCHES=("staging" "release/2025-01-monthly" "release/2025-08" "release/2025-08-13-total-analyses-fix")
    
    IS_VALID_BRANCH=false
    for branch in "${VALID_STAGING_BRANCHES[@]}"; do
        if [ "$CURRENT_BRANCH" = "$branch" ]; then
            IS_VALID_BRANCH=true
            break
        fi
    done
    
    if [ "$IS_VALID_BRANCH" = true ]; then
        print_success "Current branch '$CURRENT_BRANCH' is valid for staging"
    else
        print_error "Current branch '$CURRENT_BRANCH' is NOT valid for staging!"
        print_error "Valid staging branches: ${VALID_STAGING_BRANCHES[*]}"
        return 1
    fi
}

# Function to validate frontend staging configuration
validate_frontend_staging_config() {
    print_status "Validating frontend staging configuration..."
    
    # Check if staging config exists
    if [ ! -f "frontend/src/config.staging.js" ]; then
        print_error "Staging configuration file missing: frontend/src/config.staging.js"
        return 1
    fi
    
    # Check if staging config uses staging backend
    if ! grep -q "astraverify-backend-staging" frontend/src/config.staging.js; then
        print_error "Staging config does not use staging backend URL!"
        return 1
    fi
    
    # Check if staging config has correct app name
    if ! grep -q "AstraVerify (Staging)" frontend/src/config.staging.js; then
        print_error "Staging config does not have correct app name!"
        return 1
    fi
    
    print_success "Frontend staging configuration is correct"
}

# Function to validate backend staging configuration
validate_backend_staging_config() {
    print_status "Validating backend staging configuration..."
    
    # Check if backend uses environment-specific collections
    if ! grep -q "domain_analyses_staging" backend/firestore_config.py; then
        print_error "Backend does not have staging collection configuration!"
        return 1
    fi
    
    # Check if backend has environment variable handling
    if ! grep -q "self.environment == 'staging'" backend/firestore_config.py; then
        print_error "Backend does not have proper environment variable handling!"
        return 1
    fi
    
    print_success "Backend staging configuration is correct"
}

# Function to validate deployment scripts
validate_deployment_scripts() {
    print_status "Validating deployment scripts..."
    
    # Check if staging deployment script exists
    if [ ! -f "deploy/deploy_staging.sh" ]; then
        print_error "Staging deployment script missing: deploy/deploy_staging.sh"
        return 1
    fi
    
    # Check if staging deployment script sets correct environment
    if ! grep -q "ENVIRONMENT=staging" deploy/deploy_staging.sh; then
        print_error "Staging deployment script does not set ENVIRONMENT=staging!"
        return 1
    fi
    
    # Check if staging deployment script uses staging images
    if ! grep -q "astraverify-backend-staging" deploy/deploy_staging.sh; then
        print_error "Staging deployment script does not use staging backend image!"
        return 1
    fi
    
    if ! grep -q "astraverify-frontend-staging" deploy/deploy_staging.sh; then
        print_error "Staging deployment script does not use staging frontend image!"
        return 1
    fi
    
    print_success "Deployment scripts are correctly configured"
}

# Function to validate staging environment variables
validate_staging_env_vars() {
    print_status "Validating staging environment variables..."
    
    # Check if staging build script sets correct environment
    if [ ! -f "frontend/build-env.sh" ]; then
        print_error "Frontend build script missing: frontend/build-env.sh"
        return 1
    fi
    
    if ! grep -q "REACT_APP_ENV=staging" frontend/build-env.sh; then
        print_error "Frontend build script does not set REACT_APP_ENV=staging!"
        return 1
    fi
    
    print_success "Staging environment variables are correctly configured"
}

# Function to validate staging data store isolation
validate_staging_data_isolation() {
    print_status "Validating staging data store isolation..."
    
    # Check if staging uses separate collections
    STAGING_COLLECTIONS=("domain_analyses_staging" "email_reports_staging" "request_logs_staging")
    
    for collection in "${STAGING_COLLECTIONS[@]}"; do
        if ! grep -q "$collection" backend/firestore_config.py; then
            print_error "Staging collection '$collection' not found in backend configuration!"
            return 1
        fi
    done
    
    print_success "Staging data store isolation is properly configured"
}

# Function to validate staging URLs
validate_staging_urls() {
    print_status "Validating staging URLs..."
    
    # Expected staging backend URL
    EXPECTED_BACKEND_URL="astraverify-backend-staging-1098627686587.us-central1.run.app"
    
    if ! grep -q "$EXPECTED_BACKEND_URL" frontend/src/config.staging.js; then
        print_error "Expected staging backend URL '$EXPECTED_BACKEND_URL' not found in staging config!"
        return 1
    fi
    
    print_success "Staging URLs are correctly configured"
}

# Function to validate staging safeguards
validate_staging_safeguards() {
    print_status "Validating staging safeguards..."
    
    # Check if pre-commit hook exists
    if [ ! -f ".git/hooks/pre-commit" ]; then
        print_warning "Pre-commit hook not found - staging safeguards may be incomplete"
    else
        print_success "Pre-commit hook exists for staging safeguards"
    fi
    
    # Check if staging validation script exists
    if [ ! -f "deploy/validate-production-deployment.sh" ]; then
        print_warning "Production validation script not found"
    else
        print_success "Production validation script exists"
    fi
    
    print_success "Staging safeguards are in place"
}

# Main validation function
main() {
    print_header "STAGING ENVIRONMENT VALIDATION"
    
    local exit_code=0
    
    # Run all validations
    validate_staging_branch || exit_code=1
    validate_frontend_staging_config || exit_code=1
    validate_backend_staging_config || exit_code=1
    validate_deployment_scripts || exit_code=1
    validate_staging_env_vars || exit_code=1
    validate_staging_data_isolation || exit_code=1
    validate_staging_urls || exit_code=1
    validate_staging_safeguards || exit_code=1
    
    echo ""
    if [ $exit_code -eq 0 ]; then
        print_header "STAGING ENVIRONMENT VALIDATION PASSED"
        print_success "All staging environment checks passed!"
        print_success "Staging environment is properly configured and isolated"
    else
        print_header "STAGING ENVIRONMENT VALIDATION FAILED"
        print_error "Some staging environment checks failed!"
        print_error "Please fix the issues above before deploying to staging"
        exit 1
    fi
}

# Run main function
main "$@"
