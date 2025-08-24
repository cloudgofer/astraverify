#!/bin/bash

# Exit on any error
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
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

# Check if we're in the right directory
if [ ! -d "frontend" ] || [ ! -d "backend" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

print_status "Fixing frontend and backend deployment..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed. Please install npm first."
    exit 1
fi

# Navigate to frontend directory
cd frontend

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    print_status "Installing frontend dependencies..."
    npm install
fi

# Build the frontend
print_status "Building frontend..."
npm run build

# Navigate back to project root
cd ..

# Check if backend requirements are met
print_status "Checking backend setup..."
cd backend

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
print_status "Installing backend dependencies..."
source venv/bin/activate
pip install -r requirements.txt

# Navigate back to project root
cd ..

print_status "Frontend and backend are ready for deployment!"
print_status "To deploy to GCP, you'll need to:"
print_status "1. Install Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
print_status "2. Run: gcloud auth login"
print_status "3. Run: gcloud config set project YOUR_PROJECT_ID"
print_status "4. Run: ./deploy/deploy_production.sh (for production) or ./deploy/deploy_staging.sh (for staging)"

print_status "For local development:"
print_status "Frontend: cd frontend && npm start"
print_status "Backend: cd backend && source venv/bin/activate && python app.py" 