#!/bin/bash

# Local development script with environment-specific configuration
# This script builds and runs the application for local development

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

print_status "Starting local development environment..."

# Check if backend is running
if ! curl -s http://localhost:8080/api/health > /dev/null 2>&1; then
    print_warning "Backend not running on localhost:8080"
    print_status "Starting backend..."
    ./start_backend_with_email.sh &
    BACKEND_PID=$!
    
    # Wait for backend to start
    print_status "Waiting for backend to start..."
    for i in {1..30}; do
        if curl -s http://localhost:8080/api/health > /dev/null 2>&1; then
            print_status "Backend is running"
            break
        fi
        sleep 1
    done
    
    if [ $i -eq 30 ]; then
        print_error "Backend failed to start"
        exit 1
    fi
else
    print_status "Backend is already running"
fi

# Build frontend for local environment
print_status "Building frontend for local environment..."
cd frontend
./build-env.sh local
cd ..

# Start frontend development server
print_status "Starting frontend development server..."
cd frontend
npm start

# Cleanup function
cleanup() {
    print_status "Shutting down local development environment..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Wait for user to stop
print_status "Local development environment is running"
print_status "Frontend: http://localhost:3000"
print_status "Backend: http://localhost:8080"
print_status "Press Ctrl+C to stop"
wait 