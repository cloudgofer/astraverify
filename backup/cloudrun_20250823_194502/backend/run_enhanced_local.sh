#!/bin/bash

# Enhanced DKIM Selector Management System - Local Runner
# This script sets up and runs the enhanced DKIM system locally

set -e

echo "🚀 AstraVerify Enhanced DKIM System - Local Setup"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "dkim_selector_manager.py" ]; then
    echo -e "${RED}Error: Please run this script from the backend directory${NC}"
    exit 1
fi

# Set environment variables for local testing
echo -e "${BLUE}Setting up environment variables...${NC}"
export ENVIRONMENT=local
export GOOGLE_OAUTH_CLIENT_ID="your-google-oauth-client-id.apps.googleusercontent.com"
export GOOGLE_OAUTH_CLIENT_SECRET="your-google-oauth-client-secret"
export JWT_SECRET_KEY="astraverify-local-jwt-secret-key-2024"
export EMAIL_PASSWORD="your-email-password"

echo -e "${GREEN}Environment variables set for local testing${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
pip install -r requirements_enhanced.txt

# Test the system
echo -e "${BLUE}Running system tests...${NC}"
python test_enhanced_dkim.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
else
    echo -e "${RED}❌ Some tests failed. Please check the implementation.${NC}"
    exit 1
fi

# Start the enhanced backend
echo -e "${BLUE}Starting Enhanced DKIM Backend...${NC}"
echo -e "${GREEN}Server will be available at: http://localhost:5001${NC}"
echo -e "${GREEN}Admin UI: http://localhost:5001/admin/ui/login${NC}"
echo -e "${GREEN}Health Check: http://localhost:5001/api/health${NC}"
echo -e "${GREEN}Test Domain: http://localhost:5001/api/check?domain=google.com${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Run the enhanced application
python app_enhanced_dkim.py
