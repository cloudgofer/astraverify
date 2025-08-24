#!/bin/bash

# Exit on any error
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_header "AstraVerify Setup Script"

print_status "Checking system requirements..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js first:"
    print_error "https://nodejs.org/en/download/"
    exit 1
fi

print_status "Node.js version: $(node --version)"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed. Please install npm first."
    exit 1
fi

print_status "npm version: $(npm --version)"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3 first:"
    print_error "https://www.python.org/downloads/"
    exit 1
fi

print_status "Python version: $(python3 --version)"

print_header "Setting up Frontend"

# Navigate to frontend directory
cd frontend

# Install dependencies
print_status "Installing frontend dependencies..."
npm install

# Build the frontend
print_status "Building frontend..."
npm run build

print_status "Frontend setup completed!"

cd ..

print_header "Setting up Backend"

# Navigate to backend directory
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
print_status "Installing backend dependencies..."
source venv/bin/activate
pip install -r requirements.txt

print_status "Backend setup completed!"

cd ..

print_header "Setup Complete!"

print_status "Your AstraVerify application is now ready!"
print_status ""
print_status "To run locally:"
print_status "1. Frontend: cd frontend && npm start"
print_status "2. Backend: cd backend && source venv/bin/activate && python app.py"
print_status ""
print_status "To deploy to GCP:"
print_status "1. Install Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
print_status "2. Run: gcloud auth login"
print_status "3. Run: gcloud config set project YOUR_PROJECT_ID"
print_status "4. Run: ./deploy/deploy_production.sh (for production) or ./deploy/deploy_staging.sh (for staging)"
print_status ""
print_status "To fix deployment issues:"
print_status "Run: ./deploy/fix_frontend.sh" 