#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  Email Troubleshooting Guide${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

echo -e "${YELLOW}🔍 Current Issue:${NC}"
echo "SMTP Authentication Failed (Error 535)"
echo "Server: smtp.dreamhost.com:587"
echo "Username: hi@astraverify.com"
echo ""

echo -e "${YELLOW}🔧 Possible Solutions:${NC}"
echo ""
echo "1. ${BLUE}Check DreamHost Email Settings:${NC}"
echo "   - Log into DreamHost panel"
echo "   - Go to Email → Manage Email"
echo "   - Check if hi@astraverify.com is properly configured"
echo "   - Verify the password is correct"
echo ""
echo "2. ${BLUE}Try Different SMTP Settings:${NC}"
echo "   - Server: smtp.dreamhost.com (current)"
echo "   - Alternative: mail.dreamhost.com"
echo "   - Port: 587 (current) or 465 (SSL)"
echo ""
echo "3. ${BLUE}Check Email Account Status:${NC}"
echo "   - Ensure hi@astraverify.com is active"
echo "   - Check if there are any restrictions"
echo "   - Verify SMTP is enabled for the account"
echo ""
echo "4. ${BLUE}Alternative: Use Gmail SMTP${NC}"
echo "   - Create an app password for hi@astraverify.com"
echo "   - Use smtp.gmail.com:587"
echo "   - This might be more reliable"
echo ""

echo -e "${YELLOW}📧 Test Commands:${NC}"
echo ""
echo "Test current configuration:"
echo -e "${BLUE}curl -X GET 'https://astraverify-backend-ml2mhibdvq-uc.a.run.app/api/test-email'${NC}"
echo ""
echo "Test email sending:"
echo -e "${BLUE}curl -X POST 'https://astraverify-backend-ml2mhibdvq-uc.a.run.app/api/email-report' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"email\":\"test@example.com\",\"domain\":\"cloudgofer.com\",\"analysis_result\":{\"security_score\":{\"score\":100}},\"opt_in_marketing\":false,\"timestamp\":\"2025-08-07T00:00:00Z\"}'${NC}"
echo ""

echo -e "${GREEN}🎯 Next Steps:${NC}"
echo "1. Check DreamHost email settings"
echo "2. Verify password is correct"
echo "3. Try alternative SMTP settings if needed"
echo "4. Consider using Gmail SMTP as backup"
echo ""

echo -e "${YELLOW}📞 DreamHost Support:${NC}"
echo "If issues persist, contact DreamHost support with:"
echo "- Email: hi@astraverify.com"
echo "- SMTP Server: smtp.dreamhost.com"
echo "- Port: 587"
echo "- Error: Authentication failed"
