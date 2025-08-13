#!/bin/bash

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

# Check if we're in the right directory
if [ ! -d "frontend/src" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Function to show current config
show_current_config() {
    if [ -f "frontend/src/config.js" ]; then
        echo "Current config:"
        grep "API_BASE_URL\|APP_NAME" frontend/src/config.js
    fi
}

# Function to switch to local config
switch_to_local() {
    print_status "Switching to LOCAL configuration..."
    cp frontend/src/config.local.js frontend/src/config.js
    print_status "✅ Switched to LOCAL configuration"
    show_current_config
}

# Function to switch to staging config
switch_to_staging() {
    print_status "Switching to STAGING configuration..."
    cp frontend/src/config.staging.js frontend/src/config.js 2>/dev/null || {
        print_warning "config.staging.js not found, using default staging config"
        cat > frontend/src/config.js << 'EOF'
const config = {
  // Backend API URL - STAGING environment
  API_BASE_URL: 'https://astraverify-backend-staging-ml2mhibdvq-uc.a.run.app',

  // API endpoints
  ENDPOINTS: {
    CHECK_DOMAIN: '/api/check'
  },

  // Application settings
  APP_NAME: 'AstraVerify (Staging)',
  APP_DESCRIPTION: 'Email Domain Verification Tool - Staging Environment'
};

export default config;
EOF
    }
    print_status "✅ Switched to STAGING configuration"
    show_current_config
}

# Function to switch to production config
switch_to_production() {
    print_status "Switching to PRODUCTION configuration..."
    cp frontend/src/config.production.js frontend/src/config.js
    print_status "✅ Switched to PRODUCTION configuration"
    show_current_config
}

# Main script logic
print_header "AstraVerify Config Switcher"

if [ $# -eq 0 ]; then
    echo "Usage: $0 [local|staging|production|status]"
    echo ""
    echo "Commands:"
    echo "  local      - Switch to local development config"
    echo "  staging    - Switch to staging config"
    echo "  production - Switch to production config"
    echo "  status     - Show current configuration"
    echo ""
    echo "Current configuration:"
    show_current_config
    exit 1
fi

case "$1" in
    "local")
        switch_to_local
        ;;
    "staging")
        switch_to_staging
        ;;
    "production")
        switch_to_production
        ;;
    "status")
        show_current_config
        ;;
    *)
        print_error "Invalid option: $1"
        echo "Use: local, staging, production, or status"
        exit 1
        ;;
esac

print_status "Remember to restart your frontend development server if it's running!"
