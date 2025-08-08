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

# Check if we're on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    print_error "Production deployment can only be done from main branch!"
    print_error "Current branch: $CURRENT_BRANCH"
    print_error "Please checkout main branch first: git checkout main"
    exit 1
fi

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

print_status "Starting PRODUCTION deployment to GCP..."
print_status "GCP Project ID: astraverify"
print_status "Environment: PRODUCTION"
print_status "Branch: main"
print_status "Region: us-central1"

# Confirm production deployment
echo ""
print_warning "⚠️  WARNING: This will deploy to PRODUCTION environment!"
print_warning "This will affect live users. Are you sure you want to continue?"
echo ""
read -p "Type 'yes' to confirm production deployment: " confirm

if [ "$confirm" != "yes" ]; then
    print_error "Production deployment cancelled."
    exit 1
fi

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

# Install dependencies
print_status "Installing frontend dependencies..."
npm install

# Build frontend
print_status "Building frontend..."
npm run build

if [ $? -ne 0 ]; then
    print_error "Frontend build failed"
    exit 1
fi

print_success "Frontend build completed"

# Deploy backend to Cloud Run (PRODUCTION)
print_status "Deploying backend to Cloud Run (PRODUCTION)..."
cd ../backend

# Build and push Docker image
print_status "Building and pushing Docker image..."
gcloud builds submit --tag gcr.io/astraverify/astraverify-backend

if [ $? -ne 0 ]; then
    print_error "Backend build failed"
    exit 1
fi

# Deploy to Cloud Run with production configuration
print_status "Deploying backend to Cloud Run (PRODUCTION)..."
gcloud run deploy astraverify-backend \
    --image gcr.io/astraverify/astraverify-backend \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 1Gi \
    --cpu 2 \
    --max-instances 20 \
    --set-env-vars="ENVIRONMENT=production"

if [ $? -eq 0 ]; then
    BACKEND_URL=$(gcloud run services describe astraverify-backend --region=us-central1 --format="value(status.url)")
    print_success "Backend deployed successfully at: $BACKEND_URL"
else
    print_error "Backend deployment failed"
    exit 1
fi

# Update frontend configuration with production backend URL
print_status "Updating frontend configuration with production backend URL..."
cd ../frontend

# Create production config
cat > src/config.production.js << EOF
const config = {
  // Backend API URL - PRODUCTION environment
  API_BASE_URL: '$BACKEND_URL',

  // API endpoints
  ENDPOINTS: {
    CHECK_DOMAIN: '/api/check'
  },

  // Application settings
  APP_NAME: 'AstraVerify',
  APP_DESCRIPTION: 'Email Domain Verification Tool'
};

export default config;
EOF

# Update main config to use production
cp src/config.production.js src/config.js

# Deploy frontend to Cloud Run (PRODUCTION)
print_status "Deploying frontend to Cloud Run (PRODUCTION)..."

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
print_status "Building and deploying frontend to Cloud Run (PRODUCTION)..."
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
    FRONTEND_URL=$(gcloud run services describe astraverify-frontend --region=us-central1 --format="value(status.url)")
    print_success "Frontend deployed successfully at: $FRONTEND_URL"
else
    print_error "Frontend deployment failed"
    exit 1
fi

cd ..

# Create deployment tag
DEPLOYMENT_TAG="deploy-$(date +%Y%m%d-%H%M%S)"
git tag $DEPLOYMENT_TAG
git push origin $DEPLOYMENT_TAG

print_success "PRODUCTION deployment completed successfully! 🚀"
print_status "PRODUCTION Backend URL: $BACKEND_URL"
print_status "PRODUCTION Frontend URL: $FRONTEND_URL"
print_status "Environment: PRODUCTION"
print_status "Branch: main"
print_status "Deployment Tag: $DEPLOYMENT_TAG"
print_status "Your PRODUCTION application is now live!"
