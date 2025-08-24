#!/bin/bash

# Exit on any error
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Configuration
PROJECT_ID=${1:-"astraverify"}
REGION=${2:-"us-central1"}
SERVICE_NAME="astraverify-frontend"

print_status "Deploying frontend to Cloud Run..."

# Set the project
gcloud config set project $PROJECT_ID

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

# Build and deploy to Cloud Run
print_status "Building and deploying frontend to Cloud Run..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME frontend/

# Deploy to Cloud Run
print_status "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --platform managed \
    --allow-unauthenticated \
    --region $REGION \
    --port 8080 \
    --memory 256Mi \
    --cpu 1 \
    --max-instances 10

# Get the frontend URL
FRONTEND_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")
print_status "Frontend deployed successfully at: $FRONTEND_URL"

# Update the frontend configuration with backend URL
print_status "Updating frontend configuration..."
BACKEND_URL=$(gcloud run services describe astraverify-backend --region=$REGION --format="value(status.url)")
if [ -f "frontend/src/config.js" ]; then
    sed -i.bak "s|YOUR_BACKEND_URL|$BACKEND_URL|g" frontend/src/config.js
    print_status "Frontend configuration updated with backend URL: $BACKEND_URL"
else
    print_warning "config.js not found. You may need to manually update the backend URL."
fi

print_status "Deployment completed! 🚀"
print_status "Frontend URL: $FRONTEND_URL"
print_status "Backend URL: $BACKEND_URL" 