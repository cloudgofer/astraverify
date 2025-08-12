#!/bin/bash

# AstraVerify Startup Script
# This script starts both the backend and frontend servers

echo "🚀 Starting AstraVerify..."

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo "⚠️  Port $port is already in use"
        return 1
    else
        echo "✅ Port $port is available"
        return 0
    fi
}

# Function to start backend
start_backend() {
    echo "🔧 Starting backend server on port 8080..."
    cd backend
    if [ ! -d "venv" ]; then
        echo "📦 Creating virtual environment..."
        python3 -m venv venv
    fi
    
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
    
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    
    echo "🚀 Starting Flask backend..."
    python3 app.py &
    BACKEND_PID=$!
    echo "✅ Backend started with PID: $BACKEND_PID"
    
    # Wait a moment for backend to start
    sleep 3
    
    # Test backend
    if curl -s http://localhost:8080/api/check >/dev/null 2>&1; then
        echo "✅ Backend is responding"
    else
        echo "❌ Backend failed to start properly"
        exit 1
    fi
}

# Function to start frontend
start_frontend() {
    echo "🎨 Starting frontend server on port 3000..."
    cd frontend
    
    echo "📦 Installing dependencies..."
    npm install
    
    echo "🚀 Starting React development server..."
    npm start &
    FRONTEND_PID=$!
    echo "✅ Frontend started with PID: $FRONTEND_PID"
    
    # Wait a moment for frontend to start
    sleep 5
    
    # Test frontend
    if curl -s http://localhost:3000 >/dev/null 2>&1; then
        echo "✅ Frontend is responding"
    else
        echo "❌ Frontend failed to start properly"
        exit 1
    fi
}

# Function to cleanup on exit
cleanup() {
    echo "🛑 Shutting down servers..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo "✅ Backend stopped"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        echo "✅ Frontend stopped"
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Check ports
echo "🔍 Checking port availability..."
check_port 8080 || exit 1
check_port 3000 || exit 1

# Start servers
cd /Users/home/code/astraverify
start_backend
start_frontend

echo ""
echo "🎉 AstraVerify is now running!"
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend:  http://localhost:8080"
echo ""
echo "Press Ctrl+C to stop both servers"

# Keep script running
wait
