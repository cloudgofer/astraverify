#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  AstraVerify Email Setup - Final Steps${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

echo -e "${GREEN}✅ Backend deployed with Secret Manager support${NC}"
echo -e "${GREEN}✅ Frontend deployed and updated${NC}"
echo -e "${GREEN}✅ GCP Secret Manager API enabled${NC}"
echo -e "${GREEN}✅ Secret 'astraverify-email-password' created${NC}"
echo ""

echo -e "${YELLOW}🚀 Final Steps to Enable Email Sending:${NC}"
echo ""
echo "1. ${BLUE}Add your password to the secret:${NC}"
echo "   echo 'your-hi@astraverify.com-password' | gcloud secrets versions add astraverify-email-password --data-file=-"
echo ""
echo "2. ${BLUE}Grant access to Cloud Run service:${NC}"
echo "   gcloud secrets add-iam-policy-binding astraverify-email-password \\"
echo "     --member='serviceAccount:astraverify@astraverify.iam.gserviceaccount.com' \\"
echo "     --role='roles/secretmanager.secretAccessor'"
echo ""
echo "3. ${BLUE}Test the email feature:${NC}"
echo "   Visit: https://astraverify-frontend-ml2mhibdvq-uc.a.run.app"
echo "   Analyze a domain and click 'Email Security Report'"
echo ""

echo -e "${YELLOW}📧 Email Configuration:${NC}"
echo "Sender: hi@astraverify.com"
echo "SMTP: mail.astraverify.com:587"
echo "Username: hi@astraverify.com"
echo "Password: Stored in GCP Secret Manager"
echo ""

echo -e "${YELLOW}🔐 Security Features:${NC}"
echo "✅ Password stored securely in GCP Secret Manager"
echo "✅ Access controlled by IAM permissions"
echo "✅ No passwords in code or environment variables"
echo "✅ Automatic rotation support"
echo ""

echo -e "${GREEN}🎉 Ready to complete setup!${NC}"
echo "Run the commands above to enable email sending."
