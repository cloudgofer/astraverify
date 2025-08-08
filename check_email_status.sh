#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  Email Configuration Status${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Check if EMAIL_PASSWORD is set
if [ -n "$EMAIL_PASSWORD" ]; then
    echo -e "${GREEN}✅ EMAIL_PASSWORD is configured${NC}"
    echo "Password length: ${#EMAIL_PASSWORD} characters"
else
    echo -e "${RED}❌ EMAIL_PASSWORD is not set${NC}"
    echo "Run: export EMAIL_PASSWORD='your-app-password'"
fi

echo ""
echo -e "${YELLOW}Current Email Configuration:${NC}"
echo "Sender: hi@astraverify.com"
echo "SMTP: mail.astraverify.com:587"
echo "Username: hi@astraverify.com"
echo ""

echo -e "${YELLOW}To enable email sending:${NC}"
echo "1. Use password for hi@astraverify.com"
echo "2. Run: export EMAIL_PASSWORD='your-password'"
echo "3. Run: ./deploy/deploy_to_gcp.sh astraverify"
echo ""

echo -e "${BLUE}Test URL:${NC}"
echo "https://astraverify-frontend-ml2mhibdvq-uc.a.run.app"
