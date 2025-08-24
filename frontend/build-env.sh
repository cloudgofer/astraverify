#!/bin/bash

# Environment-specific build script for frontend
# Usage: ./build-env.sh [environment]
# Environments: local, staging, production

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

# Default environment
ENVIRONMENT=${1:-"local"}

print_status "Building frontend for environment: $ENVIRONMENT"

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(local|staging|production)$ ]]; then
    print_error "Invalid environment: $ENVIRONMENT"
    print_error "Valid environments: local, staging, production"
    exit 1
fi

# Set environment variables for React build
case $ENVIRONMENT in
    "local")
        export REACT_APP_ENV=local
        export NODE_ENV=development
        print_status "Using local configuration (localhost:8080)"
        ;;
    "staging")
        export REACT_APP_ENV=staging
        export NODE_ENV=staging
        print_status "Using staging configuration"
        ;;
    "production")
        export REACT_APP_ENV=production
        export NODE_ENV=production
        print_status "Using production configuration"
        ;;
esac

# Clean previous build
print_status "Cleaning previous build..."
rm -rf build/

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    print_status "Installing dependencies..."
    npm install
fi

# Build the application
print_status "Building React application..."
npm run build

if [ $? -eq 0 ]; then
    print_status "Build completed successfully for $ENVIRONMENT environment"
    print_status "Build output: ./build/"
else
    print_error "Build failed"
    exit 1
fi
