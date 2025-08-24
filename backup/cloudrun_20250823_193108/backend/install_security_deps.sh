#!/bin/bash

echo "🔒 Installing AstraVerify IP Abuse Prevention Dependencies"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install new dependencies
echo "📥 Installing new security dependencies..."
pip install redis==5.0.1 python-dateutil==2.8.2

# Install all requirements
echo "📦 Installing all requirements..."
pip install -r requirements.txt

echo "✅ Dependencies installed successfully!"
echo ""
echo "🚀 To start the secure backend:"
echo "   source venv/bin/activate"
echo "   python app_with_security.py"
echo ""
echo "🔧 Optional: Install Redis for better rate limiting:"
echo "   brew install redis  # macOS"
echo "   sudo apt-get install redis-server  # Ubuntu"
echo "   redis-server  # Start Redis server"
