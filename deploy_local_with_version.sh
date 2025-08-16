#!/bin/bash

# Local deployment script with version tagging
# This script deploys to local environment and tags the version

set -e

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

print_status "Starting LOCAL deployment with version tagging..."

# Check if we're on main branch
CURRENT_BRANCH=$(git branch --show-current)
print_status "Current branch: $CURRENT_BRANCH"

# Check if there are uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    print_warning "There are uncommitted changes. Committing them first..."
    git add .
    git commit -m "Auto-commit before version tagging"
fi

# Increment version and create tag
print_status "Incrementing version and creating tag..."
./version.sh tag

# Get the new version
NEW_VERSION=$(cat VERSION)
print_success "Version updated to: $NEW_VERSION"

# Update frontend version file
print_status "Updating frontend version file..."
sed -i.bak "s/VERSION = '.*'/VERSION = '$NEW_VERSION'/" frontend/src/version.js
sed -i.bak "s/BUILD_DATE = '.*'/BUILD_DATE = '$(date +%Y-%m-%d)'/" frontend/src/version.js

# Commit version changes
git add frontend/src/version.js
git commit -m "Update frontend version to $NEW_VERSION"

print_status "Starting backend..."
cd backend
ENVIRONMENT=local python3 app.py &
BACKEND_PID=$!
cd ..

print_status "Starting frontend..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

print_success "Deployment completed successfully!"
print_status "Backend PID: $BACKEND_PID"
print_status "Frontend PID: $FRONTEND_PID"
print_status "Backend URL: http://localhost:8080"
print_status "Frontend URL: http://localhost:3000"
print_status "Version: $NEW_VERSION"

# Function to cleanup on exit
cleanup() {
    print_status "Stopping services..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    print_success "Services stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

print_status "Services are running. Press Ctrl+C to stop."
wait
