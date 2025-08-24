#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  AstraVerify Email Password Setup${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

echo -e "${YELLOW}Email Configuration:${NC}"
echo "Email: hi@astraverify.com"
echo "SMTP: mail.astraverify.com:587"
echo "Username: hi@astraverify.com"
echo ""

echo -e "${YELLOW}Password Storage Options:${NC}"
echo "1. ${GREEN}Environment Variable (Recommended)${NC}"
echo "   - Set for current session only"
echo "   - Command: export EMAIL_PASSWORD='your-password'"
echo ""
echo "2. ${GREEN}Shell Profile (Permanent)${NC}"
echo "   - Add to ~/.bashrc or ~/.zshrc"
echo "   - Will persist across sessions"
echo ""
echo "3. ${GREEN}GCP Secret Manager (Production)${NC}"
echo "   - Store securely in Google Cloud"
echo "   - Access via environment variable"
echo ""

echo -e "${YELLOW}Quick Setup:${NC}"
echo "Run this command with your password:"
echo -e "${BLUE}export EMAIL_PASSWORD='your-password-here'${NC}"
echo ""
echo "Then deploy:"
echo -e "${BLUE}./deploy/deploy_production.sh${NC} (for production) or ${BLUE}./deploy/deploy_staging.sh${NC} (for staging)"
echo ""

echo -e "${YELLOW}For Production (Recommended):${NC}"
echo "1. Create GCP Secret:"
echo "   gcloud secrets create astraverify-email-password --data-file=-"
echo ""
echo "2. Grant access to Cloud Run:"
echo "   gcloud secrets add-iam-policy-binding astraverify-email-password \\"
echo "     --member='serviceAccount:astraverify@astraverify.iam.gserviceaccount.com' \\"
echo "     --role='roles/secretmanager.secretAccessor'"
echo ""
echo "3. Update deployment to use secret"
echo ""

echo -e "${GREEN}Current Status:${NC}"
if [ -n "$EMAIL_PASSWORD" ]; then
    echo -e "${GREEN}✅ EMAIL_PASSWORD is set (${#EMAIL_PASSWORD} chars)${NC}"
else
    echo -e "${RED}❌ EMAIL_PASSWORD is not set${NC}"
fi
