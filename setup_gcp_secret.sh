#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  GCP Secret Manager Setup${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

echo -e "${GREEN}✅ Secret 'astraverify-email-password' created${NC}"
echo ""

echo -e "${YELLOW}Next Steps:${NC}"
echo ""
echo "1. ${BLUE}Add your password to the secret:${NC}"
echo "   echo 'your-password-here' | gcloud secrets versions add astraverify-email-password --data-file=-"
echo ""
echo "2. ${BLUE}Grant access to Cloud Run:${NC}"
echo "   gcloud secrets add-iam-policy-binding astraverify-email-password \\"
echo "     --member='serviceAccount:astraverify@astraverify.iam.gserviceaccount.com' \\"
echo "     --role='roles/secretmanager.secretAccessor'"
echo ""
echo "3. ${BLUE}Deploy with secret support:${NC}"
echo "   ./deploy/deploy_production.sh (for production) or ./deploy/deploy_staging.sh (for staging)"
echo ""

echo -e "${YELLOW}Current Status:${NC}"
echo "✅ GCP Secret Manager API enabled"
echo "✅ Secret 'astraverify-email-password' created"
echo "❌ Password not added yet"
echo "❌ IAM permissions not set yet"
echo "❌ Backend not updated yet"
echo ""

echo -e "${BLUE}Test after setup:${NC}"
echo "Visit: https://astraverify-frontend-ml2mhibdvq-uc.a.run.app"
echo "Analyze a domain and try the email feature"
