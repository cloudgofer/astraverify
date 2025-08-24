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
BUCKET_NAME="astraverify-frontend"
REGION=${2:-"us-central1"}

print_status "Deploying frontend to Google Cloud Storage..."

# Set the project
gcloud config set project $PROJECT_ID

# Create a storage bucket for hosting
print_status "Creating storage bucket..."
gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://$BUCKET_NAME || print_warning "Bucket may already exist"

# Make the bucket publicly readable
print_status "Making bucket publicly readable..."
gsutil iam ch allUsers:objectViewer gs://$BUCKET_NAME

# Configure the bucket for website hosting
print_status "Configuring bucket for website hosting..."
gsutil web set -m index.html -e 404.html gs://$BUCKET_NAME

# Upload the built frontend files
print_status "Uploading frontend files..."
gsutil -m cp -r frontend/build/* gs://$BUCKET_NAME/

# Set cache headers for static assets
print_status "Setting cache headers..."
gsutil -m setmeta -h "Cache-Control:public, max-age=31536000" gs://$BUCKET_NAME/static/**/*.js
gsutil -m setmeta -h "Cache-Control:public, max-age=31536000" gs://$BUCKET_NAME/static/**/*.css
gsutil -m setmeta -h "Cache-Control:no-cache" gs://$BUCKET_NAME/index.html

# Get the website URL
WEBSITE_URL="https://storage.googleapis.com/$BUCKET_NAME/index.html"
print_status "Frontend deployed successfully!"
print_status "Website URL: $WEBSITE_URL"
print_status "You can also access it via: https://$BUCKET_NAME.storage.googleapis.com"

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