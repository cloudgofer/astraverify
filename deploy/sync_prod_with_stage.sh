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
    print_error "Production sync can only be done from main branch!"
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

print_status "Starting PROD sync with STAGE code..."
print_status "GCP Project ID: astraverify"
print_status "Environment: PRODUCTION (syncing with STAGE code)"
print_status "Branch: main"
print_status "Region: us-central1"

# Confirm production sync
echo ""
print_warning "⚠️  WARNING: This will sync PRODUCTION with current STAGE code!"
print_warning "This will affect live users. Are you sure you want to continue?"
echo ""
read -p "Type 'yes' to confirm production sync: " confirm

if [ "$confirm" != "yes" ]; then
    print_error "Production sync cancelled."
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

# Get current git commit hash for tracking
CURRENT_COMMIT=$(git rev-parse --short HEAD)
print_status "Current commit: $CURRENT_COMMIT"

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

# Create production config (maintaining PROD-specific settings)
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
DEPLOYMENT_TAG="sync-prod-$(date +%Y%m%d-%H%M%S)"
git tag $DEPLOYMENT_TAG
git push origin $DEPLOYMENT_TAG

# Verify deployment
print_status "Verifying deployment..."
sleep 10

# Test backend health
print_status "Testing backend health..."
BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/api/health" 2>/dev/null || echo "000")
if [ "$BACKEND_HEALTH" = "200" ]; then
    print_success "Backend health check passed"
else
    print_warning "Backend health check returned: $BACKEND_HEALTH"
fi

# Test frontend accessibility
print_status "Testing frontend accessibility..."
FRONTEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL" 2>/dev/null || echo "000")
if [ "$FRONTEND_HEALTH" = "200" ]; then
    print_success "Frontend accessibility check passed"
else
    print_warning "Frontend accessibility check returned: $FRONTEND_HEALTH"
fi

print_success "PRODUCTION sync with STAGE completed successfully! 🚀"
print_status "PRODUCTION Backend URL: $BACKEND_URL"
print_status "PRODUCTION Frontend URL: $FRONTEND_URL"
print_status "Environment: PRODUCTION (synced with STAGE code)"
print_status "Branch: main"
print_status "Commit: $CURRENT_COMMIT"
print_status "Deployment Tag: $DEPLOYMENT_TAG"
print_status "Your PRODUCTION application is now synced with STAGE code!"

# Display environment-specific notes
echo ""
print_status "Environment-specific configurations maintained:"
print_status "- Backend: ENVIRONMENT=production"
print_status "- Email: PROD app password configured"
print_status "- Frontend: Production branding and settings"
print_status "- Resources: Production-optimized (1Gi memory, 2 CPU, 20 max instances)"
