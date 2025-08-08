#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
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

# Get project ID from command line argument
PROJECT_ID=${1:-"astraverify"}

print_info "Setting up Firestore for project: $PROJECT_ID"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI is not installed. Please install it first."
    print_info "Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    print_error "Not authenticated with gcloud. Please run 'gcloud auth login' first."
    exit 1
fi

# Set the project
print_info "Setting GCP project to: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# Enable Firestore API
print_info "Enabling Firestore API..."
gcloud services enable firestore.googleapis.com

# Check if Firestore database exists
print_info "Checking Firestore database status..."
if gcloud firestore databases list --format="value(name)" | grep -q "projects/$PROJECT_ID/databases/(default)"; then
    print_success "Firestore database already exists"
else
    print_info "Creating Firestore database..."
    gcloud firestore databases create --location=us-central1
fi

# Set up Firestore security rules (optional)
print_info "Setting up Firestore security rules..."
cat > firestore.rules << 'EOF'
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Allow read access to domain_analyses collection
    match /domain_analyses/{document} {
      allow read: if true;  // Public read access for analytics
      allow write: if request.auth != null || true;  // Allow writes for now
    }
  }
}
EOF

# Deploy Firestore rules using Firebase CLI
print_info "Deploying Firestore security rules..."
if command -v firebase &> /dev/null; then
    firebase deploy --only firestore:rules
else
    print_warning "Firebase CLI not found. Rules will need to be deployed manually."
    print_info "Install Firebase CLI: npm install -g firebase-tools"
    print_info "Then run: firebase deploy --only firestore:rules"
fi

# Clean up temporary file
rm firestore.rules

print_success "Firestore setup completed successfully!"
print_info "Database: projects/$PROJECT_ID/databases/(default)"
print_info "Collection: domain_analyses"
print_info "Region: us-central1"

print_info "Next steps:"
print_info "1. Deploy the updated backend with Firestore integration"
print_info "2. Test domain analysis to verify data storage"
print_info "3. Check Firestore console for stored data"
