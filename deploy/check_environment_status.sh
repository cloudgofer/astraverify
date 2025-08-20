#!/bin/bash

# Colors for output
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

print_status "Checking environment status for AstraVerify..."

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    print_error "Not authenticated with gcloud. Please run 'gcloud auth login' first."
    exit 1
fi

# Set GCP project
gcloud config set project astraverify

echo ""
print_status "=== STAGING ENVIRONMENT STATUS ==="

# Check staging backend
print_status "Checking staging backend..."
STAGING_BACKEND_URL=$(gcloud run services describe astraverify-backend-staging --region=us-central1 --format="value(status.url)" 2>/dev/null || echo "NOT_FOUND")

if [ "$STAGING_BACKEND_URL" != "NOT_FOUND" ]; then
    print_success "Staging Backend: $STAGING_BACKEND_URL"
    
    # Test staging backend health
    STAGING_BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$STAGING_BACKEND_URL/api/health" 2>/dev/null || echo "000")
    if [ "$STAGING_BACKEND_HEALTH" = "200" ]; then
        print_success "Staging Backend Health: OK"
    else
        print_warning "Staging Backend Health: $STAGING_BACKEND_HEALTH"
    fi
else
    print_error "Staging Backend: NOT DEPLOYED"
fi

# Check staging frontend
print_status "Checking staging frontend..."
STAGING_FRONTEND_URL=$(gcloud run services describe astraverify-frontend-staging --region=us-central1 --format="value(status.url)" 2>/dev/null || echo "NOT_FOUND")

if [ "$STAGING_FRONTEND_URL" != "NOT_FOUND" ]; then
    print_success "Staging Frontend: $STAGING_FRONTEND_URL"
    
    # Test staging frontend accessibility
    STAGING_FRONTEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$STAGING_FRONTEND_URL" 2>/dev/null || echo "000")
    if [ "$STAGING_FRONTEND_HEALTH" = "200" ]; then
        print_success "Staging Frontend Health: OK"
    else
        print_warning "Staging Frontend Health: $STAGING_FRONTEND_HEALTH"
    fi
else
    print_error "Staging Frontend: NOT DEPLOYED"
fi

echo ""
print_status "=== PRODUCTION ENVIRONMENT STATUS ==="

# Check production backend
print_status "Checking production backend..."
PROD_BACKEND_URL=$(gcloud run services describe astraverify-backend --region=us-central1 --format="value(status.url)" 2>/dev/null || echo "NOT_FOUND")

if [ "$PROD_BACKEND_URL" != "NOT_FOUND" ]; then
    print_success "Production Backend: $PROD_BACKEND_URL"
    
    # Test production backend health
    PROD_BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$PROD_BACKEND_URL/api/health" 2>/dev/null || echo "000")
    if [ "$PROD_BACKEND_HEALTH" = "200" ]; then
        print_success "Production Backend Health: OK"
    else
        print_warning "Production Backend Health: $PROD_BACKEND_HEALTH"
    fi
else
    print_error "Production Backend: NOT DEPLOYED"
fi

# Check production frontend
print_status "Checking production frontend..."
PROD_FRONTEND_URL=$(gcloud run services describe astraverify-frontend --region=us-central1 --format="value(status.url)" 2>/dev/null || echo "NOT_FOUND")

if [ "$PROD_FRONTEND_URL" != "NOT_FOUND" ]; then
    print_success "Production Frontend: $PROD_FRONTEND_URL"
    
    # Test production frontend accessibility
    PROD_FRONTEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$PROD_FRONTEND_URL" 2>/dev/null || echo "000")
    if [ "$PROD_FRONTEND_HEALTH" = "200" ]; then
        print_success "Production Frontend Health: OK"
    else
        print_warning "Production Frontend Health: $PROD_FRONTEND_HEALTH"
    fi
else
    print_error "Production Frontend: NOT DEPLOYED"
fi

echo ""
print_status "=== GIT STATUS ==="

# Check current branch
CURRENT_BRANCH=$(git branch --show-current)
print_status "Current Branch: $CURRENT_BRANCH"

# Check current commit
CURRENT_COMMIT=$(git rev-parse --short HEAD)
print_status "Current Commit: $CURRENT_COMMIT"

# Check if there are uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    print_warning "There are uncommitted changes in the repository"
else
    print_success "Repository is clean (no uncommitted changes)"
fi

echo ""
print_status "=== RECOMMENDATIONS ==="

if [ "$STAGING_BACKEND_URL" != "NOT_FOUND" ] && [ "$STAGING_FRONTEND_URL" != "NOT_FOUND" ]; then
    print_success "Staging environment is deployed and ready"
    print_status "You can run: ./deploy/sync_prod_with_stage.sh to sync PROD with STAGE"
else
    print_error "Staging environment is not fully deployed"
    print_status "Please deploy to staging first: ./deploy/deploy_staging.sh"
fi

if [ "$PROD_BACKEND_URL" != "NOT_FOUND" ] && [ "$PROD_FRONTEND_URL" != "NOT_FOUND" ]; then
    print_success "Production environment is deployed"
else
    print_warning "Production environment is not fully deployed"
    print_status "You can run: ./deploy/deploy_production.sh to deploy to production"
fi
