#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  AstraVerify Email Setup${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

echo -e "${YELLOW}Email Configuration:${NC}"
echo "Sender Email: hi@astraverify.com"
echo "SMTP Server: mail.astraverify.com"
echo "SMTP Port: 587"
echo "Username: hi@astraverify.com"
echo ""

echo -e "${YELLOW}To enable email sending, you need to:${NC}"
echo ""
echo "1. ${GREEN}Configure hi@astraverify.com on DreamHost${NC}"
echo "   - Email is already hosted at DreamHost"
echo "   - SMTP settings are configured"
echo ""
echo "2. ${GREEN}Set the email password${NC}"
echo "   - Use the password for hi@astraverify.com"
echo "   - Set it as environment variable"
echo ""
echo "3. ${GREEN}Set the environment variable${NC}"
echo "   Run this command with your email password:"
echo ""
echo -e "${BLUE}export EMAIL_PASSWORD='your-email-password'${NC}"
echo ""
echo "5. ${GREEN}Deploy with email enabled${NC}"
echo "   Run: ./deploy/deploy_to_gcp.sh astraverify"
echo ""
echo -e "${YELLOW}DreamHost SMTP Configuration:${NC}"
echo "✅ Email: hi@astraverify.com"
echo "✅ SMTP Server: mail.astraverify.com"
echo "✅ Port: 587 (STARTTLS)"
echo "✅ Username: hi@astraverify.com"
echo ""
echo -e "${GREEN}Current Status:${NC}"
echo "✅ Email functionality is implemented"
echo "✅ HTML email templates are ready"
echo "❌ Email password not configured (emails will be queued but not sent)"
echo ""
echo -e "${BLUE}Test the email feature:${NC}"
echo "1. Visit: https://astraverify-frontend-ml2mhibdvq-uc.a.run.app"
echo "2. Analyze a domain"
echo "3. Click 'Email Security Report'"
echo "4. Enter your email address"
echo "5. Check if email is sent (if password configured) or queued (if not)"
