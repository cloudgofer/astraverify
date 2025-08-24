#!/bin/bash

# Exit on any error
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -d "frontend" ] || [ ! -d "backend" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI is not installed. Please install it first:"
    print_error "https://cloud.google.com/sdk/docs/install"
    print_error "Or run: curl https://sdk.cloud.google.com | bash"
    exit 1
fi

# Check if firebase CLI is installed
if ! command -v firebase &> /dev/null; then
    print_warning "Firebase CLI is not installed. Installing it now..."
    npm install -g firebase-tools
fi

# Configuration
PROJECT_ID=${1:-"astraverify"}
FIREBASE_PROJECT_ID=${2:-"astraverify-prod"}
REGION=${3:-"us-central1"}
SERVICE_NAME="astraverify-backend"

print_status "Starting deployment to GCP..."
print_status "GCP Project ID: $PROJECT_ID"
print_status "Firebase Project ID: $FIREBASE_PROJECT_ID"
print_status "Region: $REGION"

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    print_error "You are not authenticated with gcloud. Please run: gcloud auth login"
    exit 1
fi

# Set the project
print_status "Setting GCP project..."
gcloud config set project $PROJECT_ID

# Enable required APIs
print_status "Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Prepare frontend
print_status "Preparing frontend..."
cd frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    print_status "Installing frontend dependencies..."
    npm install
fi

# Build the frontend
print_status "Building frontend..."
npm run build

cd ..

# Deploy backend to Cloud Run
print_status "Deploying backend to Cloud Run..."

# Build and push the Docker image
print_status "Building and pushing Docker image..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME backend/

# Deploy to Cloud Run
print_status "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --platform managed \
    --allow-unauthenticated \
    --region $REGION \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --max-instances 10

# Get the backend URL
BACKEND_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")
print_status "Backend deployed successfully at: $BACKEND_URL"

# Update frontend configuration with backend URL
print_status "Updating frontend configuration with backend URL..."
if [ -f "frontend/src/config.js" ]; then
    # Create backup
    cp frontend/src/config.js frontend/src/config.js.backup
    # Update the backend URL
    sed -i.bak "s|https://astraverify-backend-ml2mhibdvq-uc.a.run.app|$BACKEND_URL|g" frontend/src/config.js
    print_status "Frontend configuration updated with backend URL: $BACKEND_URL"
else
    print_warning "config.js not found. You may need to manually update the backend URL in your frontend code."
fi

# Deploy frontend to Cloud Run
print_status "Deploying frontend to Cloud Run..."
FRONTEND_SERVICE_NAME="astraverify-frontend"

# Create a simple nginx Dockerfile for serving static files
print_status "Creating nginx configuration for static hosting..."
cat > frontend/Dockerfile << 'EOF'
FROM nginx:alpine
COPY build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
EOF

# Create nginx configuration
cat > frontend/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    
    server {
        listen 8080;
        server_name localhost;
        root /usr/share/nginx/html;
        index index.html;
        
        # Handle React Router
        location / {
            try_files $uri $uri/ /index.html;
        }
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
        
        # Don't cache HTML files
        location ~* \.html$ {
            add_header Cache-Control "no-cache, no-store, must-revalidate";
        }
    }
}
EOF

# Build and deploy frontend to Cloud Run
print_status "Building and deploying frontend to Cloud Run..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$FRONTEND_SERVICE_NAME frontend/

# Deploy to Cloud Run
print_status "Deploying frontend to Cloud Run..."
gcloud run deploy $FRONTEND_SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$FRONTEND_SERVICE_NAME \
    --platform managed \
    --allow-unauthenticated \
    --region $REGION \
    --port 8080 \
    --memory 256Mi \
    --cpu 1 \
    --max-instances 10

# Get the frontend URL
FRONTEND_URL=$(gcloud run services describe $FRONTEND_SERVICE_NAME --region=$REGION --format="value(status.url)")

print_status "Deployment completed successfully! 🚀"
print_status "Backend URL: $BACKEND_URL"
print_status "Frontend URL: $FRONTEND_URL"

# Clean up temporary files
rm -f frontend/Dockerfile frontend/nginx.conf

print_status "Your application is now deployed and ready to use!"
