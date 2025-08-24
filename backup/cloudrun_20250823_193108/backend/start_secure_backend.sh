#!/bin/bash

echo "🔒 Starting AstraVerify Secure Backend"

# Set environment variables
export ENVIRONMENT="local"
export ADMIN_API_KEY="astraverify-admin-2024"

# Optional: Set Redis URL if Redis is available
# export REDIS_URL="redis://localhost:6379"

# Optional: Set API keys for testing
export VALID_API_KEYS="test-api-key-1,test-api-key-2"
export PREMIUM_IPS="127.0.0.1,::1"

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if Redis is available
echo "🔍 Checking Redis availability..."
python -c "import redis; r = redis.Redis(); r.ping(); print('✅ Redis is available')" 2>/dev/null || echo "⚠️  Redis not available, using in-memory rate limiting"

# Start the secure backend
echo "🚀 Starting secure backend on http://localhost:8080"
echo "📊 Admin Dashboard: Use X-Admin-API-Key: astraverify-admin-2024"
echo "🔧 Press Ctrl+C to stop"
echo ""

python app_with_security.py
