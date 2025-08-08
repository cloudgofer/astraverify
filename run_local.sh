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

print_header "AstraVerify Local Development"

# Check if we're in the right directory
if [ ! -d "frontend" ] || [ ! -d "backend" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Function to cleanup on exit
cleanup() {
    print_status "Shutting down services..."
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    print_status "Services stopped."
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

print_status "Starting AstraVerify services locally..."

# Start backend
print_status "Starting backend server..."
cd backend

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    print_warning "Virtual environment not found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

# Start backend in background
python app.py &
BACKEND_PID=$!
print_status "Backend started with PID: $BACKEND_PID"

cd ..

# Wait a moment for backend to start
sleep 2

# Start frontend
print_status "Starting frontend development server..."
cd frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    print_status "Installing frontend dependencies..."
    npm install
fi

# Start frontend in background
npm start &
FRONTEND_PID=$!
print_status "Frontend started with PID: $FRONTEND_PID"

cd ..

print_status "Services are starting up..."
print_status "Backend will be available at: http://localhost:8080"
print_status "Frontend will be available at: http://localhost:3000"
print_status ""
print_status "Press Ctrl+C to stop all services"

# Wait for both processes
wait 