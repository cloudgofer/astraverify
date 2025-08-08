#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  Complete Email Setup${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

echo -e "${GREEN}✅ IAM permissions set successfully!${NC}"
echo "Service Account: 1098627686587-compute@developer.gserviceaccount.com"
echo "Role: roles/secretmanager.secretAccessor"
echo ""

echo -e "${YELLOW}🚀 Final Step: Add Password to Secret${NC}"
echo ""
echo "Run this command with your actual password:"
echo ""
echo -e "${BLUE}echo 'your-hi@astraverify.com-password' | gcloud secrets versions add astraverify-email-password --data-file=-${NC}"
echo ""
echo "Replace 'your-hi@astraverify.com-password' with the actual password for hi@astraverify.com"
echo ""

echo -e "${YELLOW}📧 After adding the password:${NC}"
echo "1. Visit: https://astraverify-frontend-ml2mhibdvq-uc.a.run.app"
echo "2. Analyze any domain (e.g., cloudgofer.com)"
echo "3. Click '📧 Email Security Report'"
echo "4. Enter your email address"
echo "5. Submit the form"
echo ""

echo -e "${GREEN}🎉 Email functionality will be fully operational!${NC}"
echo ""

echo -e "${YELLOW}🔐 Security Status:${NC}"
echo "✅ GCP Secret Manager API enabled"
echo "✅ Secret 'astraverify-email-password' created"
echo "✅ IAM permissions granted"
echo "✅ Backend deployed with Secret Manager support"
echo "❌ Password not added yet (final step above)"
echo ""

echo -e "${BLUE}Quick Test Command:${NC}"
echo "curl -X POST https://astraverify-backend-ml2mhibdvq-uc.a.run.app/api/email-report \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"email\":\"test@example.com\",\"domain\":\"cloudgofer.com\",\"analysis_result\":{\"security_score\":{\"score\":100}},\"opt_in_marketing\":false,\"timestamp\":\"2025-08-07T00:00:00Z\"}'"
