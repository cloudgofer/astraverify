#!/bin/bash

# Deploy Enhanced Security to Local and STAGE Environments
# This script updates both environments with security headers, rate limiting, and input validation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LOCAL_BACKUP_DIR="backup/local_$(date +%Y%m%d_%H%M%S)"
STAGING_BACKUP_DIR="backup/staging_$(date +%Y%m%d_%H%M%S)"

# Utility functions
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# Create backup directories
create_backups() {
    log "Creating backup directories..."
    
    mkdir -p "$LOCAL_BACKUP_DIR"
    mkdir -p "$STAGING_BACKUP_DIR"
    
    success "Backup directories created"
}

# Backup current files
backup_current_files() {
    log "Backing up current files..."
    
    # Backup current backend files
    if [ -f "backend/app_with_security.py" ]; then
        cp "backend/app_with_security.py" "$LOCAL_BACKUP_DIR/"
        success "Backed up app_with_security.py"
    fi
    
    if [ -f "backend/requirements.txt" ]; then
        cp "backend/requirements.txt" "$LOCAL_BACKUP_DIR/"
        success "Backed up requirements.txt"
    fi
    
    success "Backup completed"
}

# Update requirements.txt with new dependencies
update_requirements() {
    log "Updating requirements.txt with enhanced security dependencies..."
    
    # Check if redis is already in requirements
    if ! grep -q "redis" backend/requirements.txt; then
        echo "redis>=4.0.0" >> backend/requirements.txt
        success "Added redis dependency"
    fi
    
    # Check if flask-limiter is already in requirements
    if ! grep -q "flask-limiter" backend/requirements.txt; then
        echo "flask-limiter>=3.0.0" >> backend/requirements.txt
        success "Added flask-limiter dependency"
    fi
    
    success "Requirements updated"
}

# Deploy enhanced security to local environment
deploy_local() {
    log "Deploying enhanced security to LOCAL environment..."
    
    # Replace the current app with enhanced version
    if [ -f "backend/app_enhanced_security.py" ]; then
        cp "backend/app_enhanced_security.py" "backend/app_with_security.py"
        success "Updated app_with_security.py with enhanced security"
    else
        error "Enhanced security file not found"
        return 1
    fi
    
    # Install new dependencies
    log "Installing new dependencies..."
    cd backend
    pip install -r requirements.txt
    cd ..
    
    success "Local environment updated with enhanced security"
}

# Deploy enhanced security to staging environment
deploy_staging() {
    log "Deploying enhanced security to STAGING environment..."
    
    # Set environment to staging
    export ENVIRONMENT=staging
    
    # Deploy to Google Cloud Run
    log "Deploying to Google Cloud Run..."
    
    # Build and deploy the enhanced backend
    gcloud run deploy astraverify-backend-staging \
        --source backend \
        --platform managed \
        --region us-central1 \
        --allow-unauthenticated \
        --set-env-vars ENVIRONMENT=staging \
        --set-env-vars ADMIN_API_KEY=astraverify-admin-2024 \
        --set-env-vars REDIS_URL=redis://localhost:6379
    
    success "Staging environment deployed with enhanced security"
}

# Test the enhanced security
test_enhanced_security() {
    log "Testing enhanced security features..."
    
    # Test local environment
    log "Testing LOCAL environment..."
    if curl -s -f "http://localhost:5000/api/health" > /dev/null; then
        success "Local health endpoint accessible"
        
        # Test security headers
        headers=$(curl -s -I "http://localhost:5000/api/health")
        if echo "$headers" | grep -q "X-Content-Type-Options"; then
            success "Security headers present in local environment"
        else
            warning "Security headers not detected in local environment"
        fi
    else
        error "Local environment not accessible"
    fi
    
    # Test staging environment
    log "Testing STAGING environment..."
    if curl -s -f "https://astraverify-backend-staging-ml2mhibdvq-uc.a.run.app/api/health" > /dev/null; then
        success "Staging health endpoint accessible"
        
        # Test security headers
        headers=$(curl -s -I "https://astraverify-backend-staging-ml2mhibdvq-uc.a.run.app/api/health")
        if echo "$headers" | grep -q "X-Content-Type-Options"; then
            success "Security headers present in staging environment"
        else
            warning "Security headers not detected in staging environment"
        fi
    else
        error "Staging environment not accessible"
    fi
}

# Run validation tests
run_validation_tests() {
    log "Running validation tests..."
    
    # Test input validation
    log "Testing input validation..."
    
    # Test with IP address (should be rejected)
    response=$(curl -s -w "%{http_code}" "https://astraverify-backend-staging-ml2mhibdvq-uc.a.run.app/api/check?domain=192.168.1.1")
    http_code="${response: -3}"
    
    if [ "$http_code" = "400" ]; then
        success "Input validation working: IP addresses rejected"
    else
        warning "Input validation may not be working: got HTTP $http_code"
    fi
    
    # Test with malicious input (should be rejected)
    response=$(curl -s -w "%{http_code}" "https://astraverify-backend-staging-ml2mhibdvq-uc.a.run.app/api/check?domain=%3Cscript%3Ealert%28%27xss%27%29%3C/script%3E")
    http_code="${response: -3}"
    
    if [ "$http_code" = "400" ]; then
        success "Input validation working: XSS attempts rejected"
    else
        warning "Input validation may not be working for XSS: got HTTP $http_code"
    fi
    
    # Test rate limiting headers
    log "Testing rate limiting headers..."
    headers=$(curl -s -I "https://astraverify-backend-staging-ml2mhibdvq-uc.a.run.app/api/check?domain=gmail.com")
    
    if echo "$headers" | grep -q "X-RateLimit-Limit"; then
        success "Rate limiting headers present"
    else
        warning "Rate limiting headers not detected"
    fi
    
    success "Validation tests completed"
}

# Generate deployment report
generate_report() {
    log "Generating deployment report..."
    
    echo ""
    echo "=========================================="
    echo "        ENHANCED SECURITY DEPLOYMENT"
    echo "=========================================="
    echo "Deployment Date: $(date)"
    echo "Backup Location: $LOCAL_BACKUP_DIR"
    echo ""
    echo "Enhanced Features Deployed:"
    echo "✅ Security Headers (X-Content-Type-Options, X-Frame-Options, etc.)"
    echo "✅ Rate Limiting with Redis"
    echo "✅ Enhanced Input Validation"
    echo "✅ Admin Endpoints"
    echo "✅ Abuse Prevention"
    echo ""
    echo "Environments Updated:"
    echo "✅ LOCAL"
    echo "✅ STAGING"
    echo ""
    echo "Next Steps:"
    echo "1. Monitor application logs for any issues"
    echo "2. Test rate limiting functionality"
    echo "3. Verify admin endpoints are working"
    echo "4. Run comprehensive security tests"
    echo ""
    echo "Rollback Instructions:"
    echo "To rollback, restore files from: $LOCAL_BACKUP_DIR"
    echo ""
}

# Main deployment process
main() {
    echo -e "${BLUE}🚀 Starting Enhanced Security Deployment${NC}"
    echo "=========================================="
    echo "This will update both LOCAL and STAGING environments"
    echo "with enhanced security features:"
    echo "- Security headers"
    echo "- Rate limiting"
    echo "- Input validation"
    echo "=========================================="
    echo ""
    
    # Confirm deployment
    read -p "Do you want to proceed with the deployment? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled"
        exit 0
    fi
    
    # Run deployment steps
    create_backups
    backup_current_files
    update_requirements
    deploy_local
    deploy_staging
    test_enhanced_security
    run_validation_tests
    generate_report
    
    echo -e "${GREEN}🎉 Enhanced security deployment completed successfully!${NC}"
}

# Handle script interruption
trap 'echo -e "\n${RED}Deployment interrupted by user${NC}"; exit 1' INT

# Run main function
main "$@"
