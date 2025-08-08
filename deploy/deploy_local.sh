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

print_status "Starting LOCAL development setup..."
print_status "Environment: LOCAL"
print_status "This will start both frontend and backend locally"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install it first."
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install it first."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed. Please install it first."
    exit 1
fi

print_status "Setting up LOCAL development environment..."

# Setup frontend
print_status "Setting up frontend..."
cd frontend

# Install dependencies
print_status "Installing frontend dependencies..."
npm install

if [ $? -ne 0 ]; then
    print_error "Frontend dependencies installation failed"
    exit 1
fi

print_success "Frontend dependencies installed"

# Create local config
print_status "Creating local configuration..."
cat > src/config.local.js << EOF
const config = {
  // Backend API URL - LOCAL environment
  API_BASE_URL: 'http://localhost:8080',

  // API endpoints
  ENDPOINTS: {
    CHECK_DOMAIN: '/api/check'
  },

  // Application settings
  APP_NAME: 'AstraVerify (Local)',
  APP_DESCRIPTION: 'Email Domain Verification Tool - Local Development'
};

export default config;
EOF

# Update main config to use local
cp src/config.local.js src/config.js

cd ..

# Setup backend
print_status "Setting up backend..."
cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
print_status "Installing backend dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    print_error "Backend dependencies installation failed"
    exit 1
fi

print_success "Backend dependencies installed"

cd ..

print_success "LOCAL development setup completed! 🚀"
print_status "Environment: LOCAL"
print_status "Frontend: http://localhost:3000"
print_status "Backend: http://localhost:8080"
print_status ""
print_status "To start the application:"
print_status "1. Backend: cd backend && source venv/bin/activate && python app.py"
print_status "2. Frontend: cd frontend && npm start"
print_status ""
print_status "Or use the run_local.sh script: ./run_local.sh"
