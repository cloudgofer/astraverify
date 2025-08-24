#!/bin/bash

# AstraVerify Production Deployment Validation
# Ensures all configurations are correct before deploying to production

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

# Function to validate frontend configuration
validate_frontend_config() {
    print_status "Validating frontend configuration..."
    
    # Check App.js import
    if grep -q "import config from './config.local'" frontend/src/App.js; then
        print_error "App.js is importing from config.local - this will break production!"
        print_error "Please fix the import to use './config' instead of './config.local'"
        return 1
    fi
    
    if grep -q "import config from './config'" frontend/src/App.js; then
        print_success "App.js is correctly importing from config"
    else
        print_error "App.js import configuration is unclear"
        return 1
    fi
    
    # Check configuration files
    if [ ! -f "frontend/src/config.js" ]; then
        print_error "frontend/src/config.js is missing"
        return 1
    fi
    
    if [ ! -f "frontend/src/config.production.js" ]; then
        print_error "frontend/src/config.production.js is missing"
        return 1
    fi
    
    # Validate production config content
    if grep -q "AstraVerify (Local)" frontend/src/config.production.js; then
        print_error "Production config contains 'AstraVerify (Local)' - this is incorrect!"
        return 1
    fi
    
    if grep -q "AstraVerify" frontend/src/config.production.js && ! grep -q "Local\|Staging" frontend/src/config.production.js; then
        print_success "Production config has correct app name"
    else
        print_error "Production config should have 'AstraVerify' app name (without Local/Staging)"
        return 1
    fi
    
    print_success "Frontend configuration validation passed"
}

# Function to validate backend configuration
validate_backend_config() {
    print_status "Validating backend configuration..."
    
    # Check Dockerfile
    if [ ! -f "backend/Dockerfile" ]; then
        print_error "backend/Dockerfile is missing"
        return 1
    fi
    
    if grep -q "app_enhanced_dkim.py" backend/Dockerfile; then
        print_error "Backend Dockerfile is using app_enhanced_dkim.py - this will break statistics!"
        print_error "Please fix the CMD to use 'app_with_security.py'"
        return 1
    fi
    
    if grep -q "app_with_security.py" backend/Dockerfile; then
        print_success "Backend Dockerfile is correctly using app_with_security.py"
    else
        print_error "Backend Dockerfile configuration is unclear"
        return 1
    fi
    
    # Check if app_with_security.py exists
    if [ ! -f "backend/app_with_security.py" ]; then
        print_error "backend/app_with_security.py is missing"
        return 1
    fi
    
    # Check if statistics endpoint exists
    if ! grep -q "@app.route.*public/statistics" backend/app_with_security.py; then
        print_error "Statistics endpoint not found in app_with_security.py"
        return 1
    fi
    
    print_success "Backend configuration validation passed"
}

# Function to validate git status
validate_git_status() {
    print_status "Validating git status..."
    
    # Check if we're on main branch
    CURRENT_BRANCH=$(git branch --show-current)
    if [ "$CURRENT_BRANCH" != "main" ]; then
        print_error "Not on main branch! Current branch: $CURRENT_BRANCH"
        print_error "Production deployments should only be done from main branch"
        return 1
    fi
    
    # Check if working directory is clean
    if [ -n "$(git status --porcelain)" ]; then
        print_error "Working directory is not clean!"
        print_error "Please commit or stash all changes before production deployment"
        return 1
    fi
    
    # Check if we're up to date with origin
    git fetch origin
    LOCAL_COMMIT=$(git rev-parse HEAD)
    REMOTE_COMMIT=$(git rev-parse origin/main)
    
    if [ "$LOCAL_COMMIT" != "$REMOTE_COMMIT" ]; then
        print_error "Local main branch is not up to date with origin/main!"
        print_error "Please pull latest changes before production deployment"
        return 1
    fi
    
    print_success "Git status validation passed"
}

# Function to validate environment variables
validate_environment_vars() {
    print_status "Validating environment variables..."
    
    # Check if we're authenticated with gcloud
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        print_error "Not authenticated with gcloud!"
        print_error "Please run 'gcloud auth login' before production deployment"
        return 1
    fi
    
    # Check if correct project is set
    CURRENT_PROJECT=$(gcloud config get-value project)
    if [ "$CURRENT_PROJECT" != "astraverify" ]; then
        print_error "Wrong project set! Current project: $CURRENT_PROJECT"
        print_error "Please set project to 'astraverify' before production deployment"
        return 1
    fi
    
    print_success "Environment variables validation passed"
}

# Function to run pre-deployment tests
run_pre_deployment_tests() {
    print_status "Running pre-deployment tests..."
    
    # Test frontend build
    print_status "Testing frontend build..."
    cd frontend
    if ! npm run build > /dev/null 2>&1; then
        print_error "Frontend build failed!"
        return 1
    fi
    cd ..
    
    print_success "Pre-deployment tests passed"
}

# Main validation function
main() {
    print_header "AstraVerify Production Deployment Validation"
    
    local has_errors=false
    
    # Run all validation checks
    if ! validate_git_status; then
        has_errors=true
    fi
    
    if ! validate_environment_vars; then
        has_errors=true
    fi
    
    if ! validate_frontend_config; then
        has_errors=true
    fi
    
    if ! validate_backend_config; then
        has_errors=true
    fi
    
    if ! run_pre_deployment_tests; then
        has_errors=true
    fi
    
    # Final result
    if [ "$has_errors" = true ]; then
        print_error "Production deployment validation failed!"
        print_error "Please fix all errors above before deploying to production"
        exit 1
    else
        print_success "Production deployment validation passed!"
        print_success "Safe to proceed with production deployment"
    fi
}

# Run main function
main "$@"
