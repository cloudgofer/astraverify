#!/bin/bash

# AstraVerify Cloud Run Production Deployment Script with Comprehensive Safety Measures
# This script ensures production environment never goes down due to misconfiguration

set -euo pipefail  # Exit on any error, undefined variables, and pipe failures

# Configuration
PROJECT_ID="astraverify"
SERVICE_NAME="astraverify-backend"
REGION="us-central1"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"
BACKUP_DIR="backup/cloudrun_$(date +%Y%m%d_%H%M%S)"
LOG_FILE="cloudrun_deployment_$(date +%Y%m%d_%H%M%S).log"

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
    
    # Check if Dockerfile exists
    if [[ ! -f "backend/Dockerfile" ]]; then
        error "Dockerfile not found in backend directory."
    fi
    
    # Check if requirements file exists
    if [[ ! -f "backend/requirements_enhanced.txt" ]]; then
        error "requirements_enhanced.txt not found in backend directory."
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
        "backend/error_handler.py"
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
    
    # Enable required APIs
    log "Enabling required APIs..."
    gcloud services enable run.googleapis.com --quiet
    gcloud services enable containerregistry.googleapis.com --quiet
    gcloud services enable firestore.googleapis.com --quiet
    
    success "GCP access validation passed"
}

create_backup() {
    log "Creating backup of current deployment..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup current service configuration if it exists
    if gcloud run services describe "$SERVICE_NAME" --region="$REGION" >/dev/null 2>&1; then
        gcloud run services describe "$SERVICE_NAME" --region="$REGION" > "$BACKUP_DIR/service_description.json" 2>/dev/null || true
        gcloud run revisions list --service="$SERVICE_NAME" --region="$REGION" > "$BACKUP_DIR/revisions_list.txt" 2>/dev/null || true
    fi
    
    # Backup current code
    cp -r backend "$BACKUP_DIR/" 2>/dev/null || true
    
    success "Backup created in $BACKUP_DIR"
}

build_and_push_image() {
    log "Building and pushing Docker image..."
    
    cd backend
    
    # Build the image
    if ! gcloud builds submit --tag "$IMAGE_NAME" --timeout=1800s; then
        error "Docker image build failed"
    fi
    
    success "Docker image built and pushed: $IMAGE_NAME"
    cd ..
}

deploy_with_rollback() {
    log "Starting Cloud Run deployment..."
    
    # Deploy with specific configuration for production reliability
    local deployment_output
    deployment_output=$(gcloud run deploy "$SERVICE_NAME" \
        --image="$IMAGE_NAME" \
        --region="$REGION" \
        --platform="managed" \
        --allow-unauthenticated \
        --port=8080 \
        --memory=1Gi \
        --cpu=1 \
        --max-instances=10 \
        --min-instances=1 \
        --concurrency=80 \
        --timeout=300 \
        --cpu-throttling \
        --execution-environment=gen2 \
        --set-env-vars="ENVIRONMENT=production" \
        --set-env-vars="ADMIN_API_KEY=astraverify-admin-2024" \
        --set-env-vars="EMAIL_SENDER=hi@astraverify.com" \
        --set-env-vars="EMAIL_SMTP_SERVER=smtp.gmail.com" \
        --set-env-vars="EMAIL_SMTP_PORT=587" \
        --set-env-vars="EMAIL_USERNAME=hi@astraverify.com" \
        --format="value(status.url)" 2>&1)
    
    if [[ $? -eq 0 ]]; then
        local service_url=$(echo "$deployment_output" | tail -1)
        success "Deployment successful. Service URL: $service_url"
        
        # Wait for deployment to be ready
        log "Waiting for deployment to be ready..."
        sleep 30
        
        # Test the new deployment
        if test_production_endpoint "$service_url"; then
            success "Production endpoint test passed"
            
            # Store the service URL for monitoring
            echo "$service_url" > .service_url
            
        else
            error "Production endpoint test failed. Rolling back..."
            rollback_deployment
        fi
    else
        error "Deployment failed: $deployment_output"
    fi
}

test_production_endpoint() {
    local service_url="$1"
    log "Testing production endpoint: $service_url"
    
    # Test health endpoint
    local health_url="$service_url/api/health"
    
    # Try multiple times with exponential backoff
    for i in {1..5}; do
        if curl -f -s --max-time 10 "$health_url" >/dev/null; then
            success "Health endpoint responding"
            
            # Test domain check endpoint
            local test_url="$service_url/api/check?domain=google.com"
            if curl -f -s --max-time 15 "$test_url" >/dev/null; then
                success "Domain check endpoint responding"
                return 0
            else
                warning "Domain check endpoint failed"
            fi
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
    
    # Get the previous revision
    local previous_revision=$(gcloud run revisions list --service="$SERVICE_NAME" --region="$REGION" --format="value(metadata.name)" --sort-by=~metadata.createTime | head -2 | tail -1)
    
    if [[ -n "$previous_revision" ]]; then
        if gcloud run services update-traffic "$SERVICE_NAME" --region="$REGION" --to-revisions="$previous_revision=100" --quiet; then
            success "Rolled back to revision: $previous_revision"
        else
            error "Failed to rollback deployment"
        fi
    else
        error "No previous revision found for rollback"
    fi
}

monitor_deployment() {
    log "Monitoring deployment for 5 minutes..."
    
    local service_url
    if [[ -f .service_url ]]; then
        service_url=$(cat .service_url)
    else
        service_url=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)")
    fi
    
    local health_url="$service_url/api/health"
    
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

cleanup_old_revisions() {
    log "Cleaning up old revisions..."
    
    # Keep only the last 5 revisions
    local revisions_to_delete=$(gcloud run revisions list --service="$SERVICE_NAME" --region="$REGION" --format="value(metadata.name)" --sort-by=~metadata.createTime | tail -n +6)
    
    if [[ -n "$revisions_to_delete" ]]; then
        echo "$revisions_to_delete" | xargs -I {} gcloud run revisions delete {} --region="$REGION" --quiet || warning "Failed to delete some old revisions"
        success "Old revisions cleaned up"
    else
        log "No old revisions to clean up"
    fi
}

setup_monitoring() {
    log "Setting up monitoring..."
    
    # Create monitoring script
    cat > scripts/cloudrun_monitor.sh << 'EOF'
#!/bin/bash
# Cloud Run monitoring script
SERVICE_NAME="astraverify-backend"
REGION="us-central1"

if [[ -f .service_url ]]; then
    SERVICE_URL=$(cat .service_url)
    curl -f -s --max-time 10 "$SERVICE_URL/api/health" >/dev/null
    if [[ $? -eq 0 ]]; then
        echo "OK"
    else
        echo "FAILED"
    fi
else
    echo "NO_URL"
fi
EOF
    
    chmod +x scripts/cloudrun_monitor.sh
    success "Monitoring setup completed"
}

# Main deployment process
main() {
    log "Starting AstraVerify Cloud Run Production Deployment with Safety Measures"
    log "Project: $PROJECT_ID"
    log "Service: $SERVICE_NAME"
    log "Region: $REGION"
    log "Image: $IMAGE_NAME"
    log "Log file: $LOG_FILE"
    
    # Pre-deployment checks
    validate_environment
    validate_dependencies
    validate_gcp_access
    
    # Create backup
    create_backup
    
    # Build and push image
    build_and_push_image
    
    # Deploy with rollback capability
    deploy_with_rollback
    
    # Monitor deployment
    monitor_deployment
    
    # Setup monitoring
    setup_monitoring
    
    # Cleanup
    cleanup_old_revisions
    
    success "Cloud Run production deployment completed successfully!"
    log "Deployment log saved to: $LOG_FILE"
    log "Backup saved to: $BACKUP_DIR"
    log "Service URL: $(cat .service_url 2>/dev/null || echo 'Not available')"
}

# Run main function
main "$@"
