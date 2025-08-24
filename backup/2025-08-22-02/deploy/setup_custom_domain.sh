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
DOMAIN="astraverify.com"
FRONTEND_SERVICE="astraverify-frontend"
BACKEND_SERVICE="astraverify-backend"

print_status "Setting up custom domain: $DOMAIN"

# Set the project
gcloud config set project $PROJECT_ID

# Enable required APIs
print_status "Enabling required APIs..."
gcloud services enable domains.googleapis.com
gcloud services enable dns.googleapis.com

# Map custom domain to frontend service
print_status "Mapping custom domain to frontend service..."
gcloud beta run domain-mappings create \
    --service $FRONTEND_SERVICE \
    --domain $DOMAIN \
    --region=$REGION \
    --force-override

# Map subdomain for backend API
print_status "Mapping api subdomain to backend service..."
gcloud beta run domain-mappings create \
    --service $BACKEND_SERVICE \
    --domain "api.$DOMAIN" \
    --region=$REGION \
    --force-override

print_status "Custom domain setup completed!"
print_status "Frontend will be available at: https://$DOMAIN"
print_status "Backend API will be available at: https://api.$DOMAIN"
print_status ""
print_status "Note: DNS propagation may take up to 24-48 hours."
print_status "You may need to configure your DNS provider to point to Google Cloud." 