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

print_status "Setting up local email configuration for AstraVerify..."

# Set environment variable for LOCAL app password
export EMAIL_PASSWORD="juek rown cptq zkpo"
export ENVIRONMENT="local"

print_success "Local email configuration set up successfully!"
print_status "Environment: LOCAL"
print_status "App Password: juek rown cptq zkpo"
print_status "SMTP Server: smtp.gmail.com:587"
print_status "Username: hi@astraverify.com"

print_status "To start the backend with email support, run:"
echo "  export EMAIL_PASSWORD='juek rown cptq zkpo'"
echo "  export ENVIRONMENT='local'"
echo "  cd backend && python app.py"

print_status "Or use the provided script:"
echo "  ./start_backend_with_email.sh"
