#!/bin/bash

# Google OAuth Setup Script for AstraVerify Enhanced DKIM System
# This script helps configure Google OAuth 2.0 for admin access

set -e

echo "🔐 AstraVerify Google OAuth Setup"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Step 1: Google Cloud Console Setup${NC}"
echo ""
echo "1. Go to https://console.cloud.google.com/"
echo "2. Create a new project or select existing project:"
echo "   - Project Name: astraverify-admin"
echo "   - Project ID: astraverify-admin-$(date +%Y%m%d)"
echo ""
echo "3. Enable the Google+ API:"
echo "   - Go to 'APIs & Services' > 'Library'"
echo "   - Search for 'Google+ API'"
echo "   - Click 'Enable'"
echo ""
echo "4. Create OAuth 2.0 credentials:"
echo "   - Go to 'APIs & Services' > 'Credentials'"
echo "   - Click 'Create Credentials' > 'OAuth 2.0 Client IDs'"
echo "   - Application type: 'Web application'"
echo "   - Name: 'AstraVerify Admin'"
echo ""
echo -e "${YELLOW}Authorized redirect URIs to add:${NC}"
echo "   - http://localhost:5001/admin/auth/callback"
echo "   - http://127.0.0.1:5001/admin/auth/callback"
echo ""
echo "5. Copy the Client ID and Client Secret"
echo ""

# Create environment file template
echo -e "${BLUE}Step 2: Environment Configuration${NC}"
echo ""

# Check if .env file exists
if [ -f ".env" ]; then
    echo -e "${YELLOW}Found existing .env file. Backing up to .env.backup${NC}"
    cp .env .env.backup
fi

# Create .env file with OAuth configuration
cat > .env << 'EOF'
# AstraVerify Enhanced DKIM - Google OAuth Configuration
# Replace these values with your actual Google OAuth credentials

# Environment
ENVIRONMENT=local

# Google OAuth 2.0 Configuration
GOOGLE_OAUTH_CLIENT_ID=your-google-oauth-client-id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your-google-oauth-client-secret
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:5001/admin/auth/callback

# JWT Configuration
JWT_SECRET_KEY=astraverify-local-jwt-secret-key-2024-change-in-production

# Email Configuration
EMAIL_PASSWORD=your-email-password

# Firestore Configuration (optional for local testing)
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json
EOF

echo -e "${GREEN}Created .env file with OAuth configuration template${NC}"
echo ""

echo -e "${BLUE}Step 3: Update Configuration${NC}"
echo ""
echo "Please update the .env file with your actual credentials:"
echo "1. Replace 'your-google-oauth-client-id' with your actual Client ID"
echo "2. Replace 'your-google-oauth-client-secret' with your actual Client Secret"
echo "3. Update EMAIL_PASSWORD if needed"
echo ""

echo -e "${BLUE}Step 4: Test Configuration${NC}"
echo ""
echo "After updating the .env file, run:"
echo "  source .env && python test_oauth_config.py"
echo ""

echo -e "${BLUE}Step 5: Start the Enhanced System${NC}"
echo ""
echo "Once configured, start the system with:"
echo "  ./run_enhanced_local.sh"
echo ""

echo -e "${GREEN}✅ OAuth setup script completed!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Follow the Google Cloud Console steps above"
echo "2. Update the .env file with your credentials"
echo "3. Test the configuration"
echo "4. Start the enhanced system"
echo ""
