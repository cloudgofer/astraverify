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

print_status "Starting STAGING deployment to GCP..."
print_status "GCP Project ID: astraverify"
print_status "Environment: STAGING"
print_status "Region: us-central1"

# Set GCP project
print_status "Setting GCP project..."
gcloud config set project astraverify

# Enable required APIs
print_status "Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable secretmanager.googleapis.com

# Prepare frontend
print_status "Preparing frontend..."
cd frontend

# Build frontend for staging environment
print_status "Building frontend for staging environment..."
./build-env.sh staging

if [ $? -ne 0 ]; then
    print_error "Frontend build failed"
    exit 1
fi

print_success "Frontend build completed for staging environment"

# Deploy backend to Cloud Run (STAGING)
print_status "Deploying backend to Cloud Run (STAGING)..."
cd ../backend

# Build and push Docker image
print_status "Building and pushing Docker image..."
gcloud builds submit --tag gcr.io/astraverify/astraverify-backend-staging

if [ $? -ne 0 ]; then
    print_error "Backend build failed"
    exit 1
fi

# Deploy to Cloud Run with staging configuration
print_status "Deploying backend to Cloud Run (STAGING)..."
gcloud run deploy astraverify-backend-staging \
    --image gcr.io/astraverify/astraverify-backend-staging \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --max-instances 10 \
    --set-env-vars="ENVIRONMENT=staging"

if [ $? -eq 0 ]; then
    BACKEND_URL=$(gcloud run services describe astraverify-backend-staging --region=us-central1 --format="value(status.url)")
    print_success "Backend deployed successfully at: $BACKEND_URL"
else
    print_error "Backend deployment failed"
    exit 1
fi

# Note: Frontend configuration is now handled by build-env.sh script
# The staging config is already set up in src/config.staging.js
cd ../frontend

# Deploy frontend to Cloud Run (STAGING)
print_status "Deploying frontend to Cloud Run (STAGING)..."

# Create nginx configuration for static hosting
print_status "Creating nginx configuration for static hosting..."
cat > nginx.conf << EOF
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    server {
        listen 8080;
        server_name localhost;
        root /usr/share/nginx/html;
        index index.html;
        
        location / {
            try_files \$uri \$uri/ /index.html;
        }
        
        location /static/ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
EOF

# Build and deploy frontend
print_status "Building and deploying frontend to Cloud Run (STAGING)..."
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
    --memory 256Mi \
    --cpu 0.5 \
    --max-instances 5

if [ $? -eq 0 ]; then
    FRONTEND_URL=$(gcloud run services describe astraverify-frontend-staging --region=us-central1 --format="value(status.url)")
    print_success "Frontend deployed successfully at: $FRONTEND_URL"
else
    print_error "Frontend deployment failed"
    exit 1
fi

cd ..

print_success "STAGING deployment completed successfully! 🚀"
print_status "STAGING Backend URL: $BACKEND_URL"
print_status "STAGING Frontend URL: $FRONTEND_URL"
print_status "Environment: STAGING"
print_status "Branch: release/2025-08"
print_status "Your STAGING application is now deployed and ready for testing!"
