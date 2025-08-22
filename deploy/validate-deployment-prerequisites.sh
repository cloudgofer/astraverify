#!/bin/bash

# AstraVerify Deployment Validation Script
# Validates configuration and environment setup before deployment

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
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

# Function to validate environment
validate_environment() {
    local environment=$1
    
    print_status "Validating environment: $environment"
    
    case $environment in
        "local")
            validate_local_environment
            ;;
        "staging")
            validate_staging_environment
            ;;
        "production")
            validate_production_environment
            ;;
        *)
            print_error "Unknown environment: $environment"
            exit 1
            ;;
    esac
}

# Function to validate local environment
validate_local_environment() {
    print_status "Checking local environment configuration..."
    
    # Check if backend is running
    if curl -s http://localhost:8080/api/check?domain=example.com > /dev/null 2>&1; then
        print_success "Backend is running on localhost:8080"
    else
        print_error "Backend is not running on localhost:8080"
        print_status "Start backend with: cd backend && python app.py"
        exit 1
    fi
    
    # Check frontend configuration
    if grep -q "localhost:8080" frontend/src/config.js; then
        print_success "Frontend configured for local development"
    else
        print_error "Frontend not configured for local development"
        print_status "Expected: API_BASE_URL: 'http://localhost:8080'"
        exit 1
    fi
    
    # Check if frontend dependencies are installed
    if [ -d "frontend/node_modules" ]; then
        print_success "Frontend dependencies installed"
    else
        print_warning "Frontend dependencies not installed"
        print_status "Run: cd frontend && npm install"
    fi
    
    # Check if backend dependencies are installed
    if [ -d "backend/venv" ]; then
        print_success "Backend virtual environment exists"
    else
        print_warning "Backend virtual environment not found"
        print_status "Run: cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    fi
}

# Function to validate staging environment
validate_staging_environment() {
    print_status "Checking staging environment configuration..."
    
    # Check staging backend URL
    local staging_backend_url="https://astraverify-backend-staging-ml2mhibdvq-uc.a.run.app"
    
    if curl -s "$staging_backend_url/api/check?domain=example.com" > /dev/null 2>&1; then
        print_success "Staging backend is accessible"
    else
        print_error "Staging backend is not accessible: $staging_backend_url"
        exit 1
    fi
    
    # Check staging frontend configuration
    if grep -q "astraverify-backend-staging" frontend/src/config.staging.js; then
        print_success "Staging frontend configuration correct"
    else
        print_error "Staging frontend configuration incorrect"
        print_status "Expected: API_BASE_URL pointing to staging backend"
        exit 1
    fi
    
    # Check Google Cloud project
    local current_project=$(gcloud config get-value project 2>/dev/null)
    if [ "$current_project" = "astraverify" ]; then
        print_success "Google Cloud project set to astraverify"
    else
        print_error "Google Cloud project not set to astraverify (current: $current_project)"
        print_status "Run: gcloud config set project astraverify"
        exit 1
    fi
}

# Function to validate production environment
validate_production_environment() {
    print_status "Checking production environment configuration..."
    
    # Check production backend URL
    local production_backend_url="https://astraverify-backend-ml2mhibdvq-uc.a.run.app"
    
    if curl -s "$production_backend_url/api/check?domain=example.com" > /dev/null 2>&1; then
        print_success "Production backend is accessible"
    else
        print_error "Production backend is not accessible: $production_backend_url"
        exit 1
    fi
    
    # Check production frontend configuration
    if grep -q "astraverify-backend-ml2mhibdvq-uc.a.run.app" frontend/src/config.production.js; then
        print_success "Production frontend configuration correct"
    else
        print_error "Production frontend configuration incorrect"
        print_status "Expected: API_BASE_URL pointing to production backend"
        exit 1
    fi
    
    # Check Google Cloud project
    local current_project=$(gcloud config get-value project 2>/dev/null)
    if [ "$current_project" = "astraverify" ]; then
        print_success "Google Cloud project set to astraverify"
    else
        print_error "Google Cloud project not set to astraverify (current: $current_project)"
        print_status "Run: gcloud config set project astraverify"
        exit 1
    fi
    
    # Check if we're on main branch for production
    local current_branch=$(git branch --show-current)
    if [ "$current_branch" = "main" ]; then
        print_success "On main branch for production deployment"
    else
        print_warning "Not on main branch (current: $current_branch)"
        print_status "Production deployments should be from main branch"
    fi
}

# Function to validate configuration files
validate_configuration_files() {
    print_status "Validating configuration files..."
    
    # Check if all config files exist
    local config_files=(
        "frontend/src/config.js"
        "frontend/src/config.staging.js"
        "frontend/src/config.production.js"
    )
    
    for config_file in "${config_files[@]}"; do
        if [ -f "$config_file" ]; then
            print_success "Configuration file exists: $config_file"
        else
            print_error "Configuration file missing: $config_file"
            exit 1
        fi
    done
    
    # Validate API_BASE_URL in each config
    validate_api_urls
}

# Function to validate API URLs in configuration files
validate_api_urls() {
    print_status "Validating API URLs in configuration files..."
    
    # Check local config
    if grep -q "localhost:8080" frontend/src/config.js; then
        print_success "Local config points to localhost:8080"
    else
        print_error "Local config does not point to localhost:8080"
    fi
    
    # Check staging config
    if grep -q "astraverify-backend-staging" frontend/src/config.staging.js; then
        print_success "Staging config points to staging backend"
    else
        print_error "Staging config does not point to staging backend"
    fi
    
    # Check production config
    if grep -q "astraverify-backend-ml2mhibdvq-uc.a.run.app" frontend/src/config.production.js; then
        print_success "Production config points to production backend"
    else
        print_error "Production config does not point to production backend"
    fi
}

# Function to validate git status
validate_git_status() {
    print_status "Validating git status..."
    
    # Check if we're in a git repository
    if [ ! -d ".git" ]; then
        print_error "Not in a git repository"
        exit 1
    fi
    
    # Check for uncommitted changes
    if [ -n "$(git status --porcelain)" ]; then
        print_warning "There are uncommitted changes"
        print_status "Consider committing changes before deployment"
    else
        print_success "No uncommitted changes"
    fi
    
    # Check if we're up to date with remote
    git fetch origin > /dev/null 2>&1
    local local_commit=$(git rev-parse HEAD)
    local remote_commit=$(git rev-parse origin/$(git branch --show-current))
    
    if [ "$local_commit" = "$remote_commit" ]; then
        print_success "Local branch is up to date with remote"
    else
        print_warning "Local branch is not up to date with remote"
        print_status "Consider pulling latest changes"
    fi
}

# Function to validate dependencies
validate_dependencies() {
    print_status "Validating dependencies..."
    
    # Check if required tools are installed
    local required_tools=("gcloud" "node" "npm" "python3")
    local optional_tools=("docker")
    
    for tool in "${required_tools[@]}"; do
        if command -v "$tool" > /dev/null 2>&1; then
            print_success "$tool is installed"
        else
            print_error "$tool is not installed"
            exit 1
        fi
    done
    
    for tool in "${optional_tools[@]}"; do
        if command -v "$tool" > /dev/null 2>&1; then
            print_success "$tool is installed"
        else
            print_warning "$tool is not installed (optional for local development)"
        fi
    done
    
    # Check gcloud authentication
    if gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        print_success "Google Cloud is authenticated"
    else
        print_error "Google Cloud is not authenticated"
        print_status "Run: gcloud auth login"
        exit 1
    fi
}

# Function to run post-deployment checks
run_post_deployment_checks() {
    local environment=$1
    local frontend_url=$2
    local backend_url=$3
    
    print_status "Running post-deployment checks for $environment..."
    
    # Wait a moment for deployment to settle
    sleep 10
    
    # Check frontend accessibility
    if curl -s "$frontend_url" > /dev/null 2>&1; then
        print_success "Frontend is accessible: $frontend_url"
    else
        print_error "Frontend is not accessible: $frontend_url"
        return 1
    fi
    
    # Check backend API
    if curl -s "$backend_url/api/check?domain=example.com" > /dev/null 2>&1; then
        print_success "Backend API is working: $backend_url"
    else
        print_error "Backend API is not working: $backend_url"
        return 1
    fi
    
    # Test domain analysis
    local test_response=$(curl -s "$backend_url/api/check?domain=google.com&progressive=true")
    if echo "$test_response" | grep -q "google.com"; then
        print_success "Domain analysis is working"
    else
        print_error "Domain analysis is not working"
        return 1
    fi
    
    print_success "All post-deployment checks passed for $environment"
}

# Main function
main() {
    local environment=$1
    
    if [ -z "$environment" ]; then
        print_error "Usage: $0 <environment>"
        print_status "Environments: local, staging, production"
        exit 1
    fi
    
    print_status "Starting deployment validation for $environment environment..."
    
    # Run all validations
    validate_dependencies
    validate_git_status
    validate_configuration_files
    validate_environment "$environment"
    
    print_success "All pre-deployment validations passed for $environment"
    print_status "Ready to deploy to $environment environment"
}

# Export functions for use in other scripts
export -f validate_environment
export -f validate_local_environment
export -f validate_staging_environment
export -f validate_production_environment
export -f validate_configuration_files
export -f validate_api_urls
export -f validate_git_status
export -f validate_dependencies
export -f run_post_deployment_checks

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
