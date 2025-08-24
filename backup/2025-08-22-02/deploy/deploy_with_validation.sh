#!/bin/bash

# AstraVerify Enhanced Deployment Script with Validation
# Includes pre-deployment validation and post-deployment checks

set -e

# Source the validation script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/validate-deployment-prerequisites.sh"

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

# Function to deploy to local environment
deploy_local() {
    print_status "Deploying to LOCAL environment..."
    
    # Validate local environment
    validate_environment "local"
    
    # Start backend if not running
    if ! curl -s http://localhost:8080/api/check?domain=example.com > /dev/null 2>&1; then
        print_status "Starting backend..."
        cd backend
        if [ ! -d "venv" ]; then
            print_status "Creating virtual environment..."
            python3 -m venv venv
        fi
        source venv/bin/activate
        pip install -r requirements.txt
        python app.py &
        BACKEND_PID=$!
        cd ..
        
        # Wait for backend to start
        print_status "Waiting for backend to start..."
        for i in {1..30}; do
            if curl -s http://localhost:8080/api/check?domain=example.com > /dev/null 2>&1; then
                print_success "Backend started successfully"
                break
            fi
            sleep 1
        done
        
        if [ $i -eq 30 ]; then
            print_error "Backend failed to start"
            exit 1
        fi
    fi
    
    # Start frontend
    print_status "Starting frontend..."
    cd frontend
    if [ ! -d "node_modules" ]; then
        print_status "Installing frontend dependencies..."
        npm install
    fi
    npm start &
    FRONTEND_PID=$!
    cd ..
    
    print_success "LOCAL deployment completed"
    print_status "Backend: http://localhost:8080"
    print_status "Frontend: http://localhost:3000"
    print_status "Press Ctrl+C to stop services"
    
    # Wait for user to stop
    trap "cleanup_local" INT
    wait
}

# Function to cleanup local deployment
cleanup_local() {
    print_status "Cleaning up local deployment..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    print_success "Local deployment stopped"
    exit 0
}

# Function to deploy to staging environment
deploy_staging() {
    print_status "Deploying to STAGING environment..."
    
    # Validate staging environment
    validate_environment "staging"
    
    # Set staging configuration
    print_status "Setting staging configuration..."
    cp frontend/src/config.staging.js frontend/src/config.js
    
    # Deploy backend to staging
    print_status "Deploying backend to staging..."
    cd backend
    gcloud builds submit --tag gcr.io/astraverify/astraverify-backend-staging
    
    if [ $? -ne 0 ]; then
        print_error "Backend build failed"
        exit 1
    fi
    
    gcloud run deploy astraverify-backend-staging \
        --image gcr.io/astraverify/astraverify-backend-staging \
        --region us-central1 \
        --platform managed \
        --allow-unauthenticated \
        --port 8080 \
        --memory 1Gi \
        --cpu 1 \
        --max-instances 10
    
    if [ $? -eq 0 ]; then
        STAGING_BACKEND_URL=$(gcloud run services describe astraverify-backend-staging --region=us-central1 --format="value(status.url)")
        print_success "Backend deployed to staging: $STAGING_BACKEND_URL"
    else
        print_error "Backend deployment failed"
        exit 1
    fi
    cd ..
    
    # Deploy frontend to staging
    print_status "Deploying frontend to staging..."
    cd frontend
    gcloud builds submit --tag gcr.io/astraverify/astraverify-frontend-staging
    
    if [ $? -ne 0 ]; then
        print_error "Frontend build failed"
        exit 1
    fi
    
    gcloud run deploy astraverify-frontend-staging \
        --image gcr.io/astraverify/astraverify-frontend-staging \
        --region us-central1 \
        --platform managed \
        --allow-unauthenticated \
        --port 8080 \
        --memory 512Mi \
        --cpu 1 \
        --max-instances 10
    
    if [ $? -eq 0 ]; then
        STAGING_FRONTEND_URL=$(gcloud run services describe astraverify-frontend-staging --region=us-central1 --format="value(status.url)")
        print_success "Frontend deployed to staging: $STAGING_FRONTEND_URL"
    else
        print_error "Frontend deployment failed"
        exit 1
    fi
    cd ..
    
    # Run post-deployment checks
    run_post_deployment_checks "staging" "$STAGING_FRONTEND_URL" "$STAGING_BACKEND_URL"
    
    # Create deployment tag
    DEPLOYMENT_TAG="staging-$(date +%Y%m%d-%H%M%S)"
    git tag $DEPLOYMENT_TAG
    git push origin $DEPLOYMENT_TAG
    
    print_success "STAGING deployment completed successfully! 🚀"
    print_status "Staging Backend URL: $STAGING_BACKEND_URL"
    print_status "Staging Frontend URL: $STAGING_FRONTEND_URL"
    print_status "Environment: STAGING"
    print_status "Branch: $(git branch --show-current)"
    print_status "Deployment Tag: $DEPLOYMENT_TAG"
}

# Function to deploy to production environment
deploy_production() {
    print_status "Deploying to PRODUCTION environment..."
    
    # Validate production environment
    validate_environment "production"
    
    # Confirm production deployment
    print_warning "You are about to deploy to PRODUCTION"
    read -p "Are you sure you want to continue? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        print_status "Production deployment cancelled"
        exit 0
    fi
    
    # Set production configuration
    print_status "Setting production configuration..."
    cp frontend/src/config.production.js frontend/src/config.js
    
    # Deploy backend to production
    print_status "Deploying backend to production..."
    cd backend
    gcloud builds submit --tag gcr.io/astraverify/astraverify-backend
    
    if [ $? -ne 0 ]; then
        print_error "Backend build failed"
        exit 1
    fi
    
    gcloud run deploy astraverify-backend \
        --image gcr.io/astraverify/astraverify-backend \
        --region us-central1 \
        --platform managed \
        --allow-unauthenticated \
        --port 8080 \
        --memory 1Gi \
        --cpu 1 \
        --max-instances 10
    
    if [ $? -eq 0 ]; then
        PRODUCTION_BACKEND_URL=$(gcloud run services describe astraverify-backend --region=us-central1 --format="value(status.url)")
        print_success "Backend deployed to production: $PRODUCTION_BACKEND_URL"
    else
        print_error "Backend deployment failed"
        exit 1
    fi
    cd ..
    
    # Deploy frontend to production
    print_status "Deploying frontend to production..."
    cd frontend
    gcloud builds submit --tag gcr.io/astraverify/astraverify-frontend
    
    if [ $? -ne 0 ]; then
        print_error "Frontend build failed"
        exit 1
    fi
    
    gcloud run deploy astraverify-frontend \
        --image gcr.io/astraverify/astraverify-frontend \
        --region us-central1 \
        --platform managed \
        --allow-unauthenticated \
        --port 8080 \
        --memory 512Mi \
        --cpu 1 \
        --max-instances 10
    
    if [ $? -eq 0 ]; then
        PRODUCTION_FRONTEND_URL=$(gcloud run services describe astraverify-frontend --region=us-central1 --format="value(status.url)")
        print_success "Frontend deployed to production: $PRODUCTION_FRONTEND_URL"
    else
        print_error "Frontend deployment failed"
        exit 1
    fi
    cd ..
    
    # Run post-deployment checks
    run_post_deployment_checks "production" "$PRODUCTION_FRONTEND_URL" "$PRODUCTION_BACKEND_URL"
    
    # Create deployment tag
    DEPLOYMENT_TAG="production-$(date +%Y%m%d-%H%M%S)"
    git tag $DEPLOYMENT_TAG
    git push origin $DEPLOYMENT_TAG
    
    print_success "PRODUCTION deployment completed successfully! 🚀"
    print_status "Production Backend URL: $PRODUCTION_BACKEND_URL"
    print_status "Production Frontend URL: $PRODUCTION_FRONTEND_URL"
    print_status "Environment: PRODUCTION"
    print_status "Branch: $(git branch --show-current)"
    print_status "Deployment Tag: $DEPLOYMENT_TAG"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 <environment> [options]"
    echo ""
    echo "Environments:"
    echo "  local       - Deploy to local development environment"
    echo "  staging     - Deploy to staging environment"
    echo "  production  - Deploy to production environment"
    echo ""
    echo "Options:"
    echo "  --validate-only  - Only run validation checks without deploying"
    echo "  --help          - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 local                    # Deploy to local environment"
    echo "  $0 staging                  # Deploy to staging environment"
    echo "  $0 production               # Deploy to production environment"
    echo "  $0 production --validate-only  # Only validate production environment"
}

# Main function
main() {
    local environment=$1
    local validate_only=false
    
    # Parse options
    while [[ $# -gt 0 ]]; do
        case $1 in
            --validate-only)
                validate_only=true
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                environment=$1
                shift
                ;;
        esac
    done
    
    if [ -z "$environment" ]; then
        print_error "No environment specified"
        show_usage
        exit 1
    fi
    
    print_status "Starting deployment process for $environment environment..."
    
    case $environment in
        "local")
            if [ "$validate_only" = true ]; then
                validate_environment "local"
                print_success "Local environment validation completed"
            else
                deploy_local
            fi
            ;;
        "staging")
            if [ "$validate_only" = true ]; then
                validate_environment "staging"
                print_success "Staging environment validation completed"
            else
                deploy_staging
            fi
            ;;
        "production")
            if [ "$validate_only" = true ]; then
                validate_environment "production"
                print_success "Production environment validation completed"
            else
                deploy_production
            fi
            ;;
        *)
            print_error "Unknown environment: $environment"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
