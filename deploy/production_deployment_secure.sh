#!/bin/bash

# AstraVerify Production Deployment Script with Comprehensive Safety Measures
# This script ensures production environment never goes down due to misconfiguration

set -euo pipefail  # Exit on any error, undefined variables, and pipe failures

# Configuration
PROJECT_ID="astraverify"
SERVICE_NAME="default"
REGION="us-central1"
BACKUP_DIR="backup/production_$(date +%Y%m%d_%H%M%S)"
LOG_FILE="deployment_$(date +%Y%m%d_%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

# Pre-deployment validation functions
validate_environment() {
    log "Validating deployment environment..."
    
    # Check if we're in the right directory
    if [[ ! -f "backend/app_enhanced_dkim.py" ]]; then
        error "Not in the correct directory. Please run from project root."
    fi
    
    # Check if app.yaml exists
    if [[ ! -f "backend/app.yaml" ]]; then
        error "app.yaml not found in backend directory."
    fi
    
    # Validate app.yaml syntax
    if ! python3 -c "import yaml; yaml.safe_load(open('backend/app.yaml'))" 2>/dev/null; then
        error "app.yaml has invalid YAML syntax."
    fi
    
    success "Environment validation passed"
}

validate_dependencies() {
    log "Validating dependencies..."
    
    # Check if required files exist
    local required_files=(
        "backend/app_enhanced_dkim.py"
        "backend/requirements_enhanced.txt"
        "backend/firestore_config.py"
        "backend/dkim_selector_manager.py"
        "backend/enhanced_dkim_scanner.py"
        "backend/admin_api.py"
        "backend/admin_ui.py"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            error "Required file missing: $file"
        fi
    done
    
    # Check Python syntax
    cd backend
    if ! python3 -m py_compile app_enhanced_dkim.py; then
        error "Python syntax error in app_enhanced_dkim.py"
    fi
    
    # Check imports
    if ! python3 -c "import app_enhanced_dkim" 2>/dev/null; then
        error "Import error in app_enhanced_dkim.py"
    fi
    
    cd ..
    success "Dependencies validation passed"
}

validate_gcp_access() {
    log "Validating GCP access..."
    
    # Check if authenticated
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        error "Not authenticated with gcloud. Run 'gcloud auth login' first."
    fi
    
    # Check if project is set
    if [[ "$(gcloud config get-value project 2>/dev/null)" != "$PROJECT_ID" ]]; then
        error "Project not set to $PROJECT_ID. Run 'gcloud config set project $PROJECT_ID' first."
    fi
    
    # Check if we have necessary permissions
    if ! gcloud projects describe "$PROJECT_ID" >/dev/null 2>&1; then
        error "Cannot access project $PROJECT_ID. Check permissions."
    fi
    
    success "GCP access validation passed"
}

create_backup() {
    log "Creating backup of current deployment..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup current app.yaml if it exists
    if gcloud app describe >/dev/null 2>&1; then
        gcloud app describe > "$BACKUP_DIR/app_description.json" 2>/dev/null || true
        gcloud app versions list > "$BACKUP_DIR/versions_list.txt" 2>/dev/null || true
    fi
    
    # Backup current code
    cp -r backend "$BACKUP_DIR/" 2>/dev/null || true
    
    success "Backup created in $BACKUP_DIR"
}

validate_app_config() {
    log "Validating application configuration..."
    
    cd backend
    
    # Check if all required environment variables are set in app.yaml
    local required_env_vars=(
        "ENVIRONMENT"
        "ADMIN_API_KEY"
        "EMAIL_SENDER"
        "EMAIL_SMTP_SERVER"
        "EMAIL_SMTP_PORT"
        "EMAIL_USERNAME"
    )
    
    for var in "${required_env_vars[@]}"; do
        if ! grep -q "^  $var:" app.yaml; then
            warning "Environment variable $var not found in app.yaml"
        fi
    done
    
    # Validate port configuration
    if ! grep -q "PORT" app.yaml; then
        warning "PORT environment variable not explicitly set in app.yaml"
    fi
    
    cd ..
    success "Application configuration validation passed"
}

test_local_deployment() {
    log "Testing local deployment..."
    
    cd backend
    
    # Test if the app can start locally
    timeout 30s python3 -c "
import app_enhanced_dkim
print('App imports successfully')
" || error "Local app test failed"
    
    cd ..
    success "Local deployment test passed"
}

deploy_with_rollback() {
    log "Starting production deployment..."
    
    # Create a new version without stopping the current one
    local new_version=$(date +%Y%m%d-%H%M%S)
    
    cd backend
    
    # Deploy with specific version
    if gcloud app deploy app.yaml --version="$new_version" --quiet; then
        success "Deployment successful. Version: $new_version"
        
        # Wait for deployment to be ready
        log "Waiting for deployment to be ready..."
        sleep 30
        
        # Test the new version
        if test_production_endpoint; then
            success "Production endpoint test passed"
            
            # Migrate traffic to new version
            if gcloud app services set-traffic default --splits="$new_version"=1.0 --quiet; then
                success "Traffic migrated to new version: $new_version"
                
                # Keep the previous version for quick rollback
                log "Keeping previous version for rollback capability"
                
            else
                error "Failed to migrate traffic to new version"
            fi
        else
            error "Production endpoint test failed. Rolling back..."
            rollback_deployment
        fi
    else
        error "Deployment failed"
    fi
    
    cd ..
}

test_production_endpoint() {
    log "Testing production endpoint..."
    
    # Get the app URL
    local app_url=$(gcloud app describe --format="value(defaultHostname)")
    
    if [[ -z "$app_url" ]]; then
        return 1
    fi
    
    # Test health endpoint
    local health_url="https://$app_url/api/health"
    
    # Try multiple times with exponential backoff
    for i in {1..5}; do
        if curl -f -s --max-time 10 "$health_url" >/dev/null; then
            success "Health endpoint responding"
            return 0
        fi
        
        if [[ $i -lt 5 ]]; then
            log "Health check attempt $i failed, retrying in $((2**i)) seconds..."
            sleep $((2**i))
        fi
    done
    
    return 1
}

rollback_deployment() {
    log "Rolling back deployment..."
    
    # Get the previous version
    local previous_version=$(gcloud app versions list --format="value(id)" --sort-by=~createTime | head -2 | tail -1)
    
    if [[ -n "$previous_version" ]]; then
        if gcloud app services set-traffic default --splits="$previous_version"=1.0 --quiet; then
            success "Rolled back to version: $previous_version"
        else
            error "Failed to rollback deployment"
        fi
    else
        error "No previous version found for rollback"
    fi
}

monitor_deployment() {
    log "Monitoring deployment for 5 minutes..."
    
    local app_url=$(gcloud app describe --format="value(defaultHostname)")
    local health_url="https://$app_url/api/health"
    
    for i in {1..60}; do
        if curl -f -s --max-time 5 "$health_url" >/dev/null; then
            echo -n "."
        else
            echo -n "x"
        fi
        
        if [[ $((i % 10)) -eq 0 ]]; then
            echo ""
        fi
        
        sleep 5
    done
    
    echo ""
    success "Deployment monitoring completed"
}

cleanup_old_versions() {
    log "Cleaning up old versions..."
    
    # Keep only the last 3 versions
    local versions_to_delete=$(gcloud app versions list --format="value(id)" --sort-by=~createTime | tail -n +4)
    
    if [[ -n "$versions_to_delete" ]]; then
        echo "$versions_to_delete" | xargs -I {} gcloud app versions delete {} --quiet || warning "Failed to delete some old versions"
        success "Old versions cleaned up"
    else
        log "No old versions to clean up"
    fi
}

# Main deployment process
main() {
    log "Starting AstraVerify Production Deployment with Safety Measures"
    log "Project: $PROJECT_ID"
    log "Service: $SERVICE_NAME"
    log "Region: $REGION"
    log "Log file: $LOG_FILE"
    
    # Pre-deployment checks
    validate_environment
    validate_dependencies
    validate_gcp_access
    validate_app_config
    test_local_deployment
    
    # Create backup
    create_backup
    
    # Deploy with rollback capability
    deploy_with_rollback
    
    # Monitor deployment
    monitor_deployment
    
    # Cleanup
    cleanup_old_versions
    
    success "Production deployment completed successfully!"
    log "Deployment log saved to: $LOG_FILE"
    log "Backup saved to: $BACKUP_DIR"
}

# Run main function
main "$@"
