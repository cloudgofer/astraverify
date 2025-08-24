#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  Add Email Password to GCP Secret${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

echo -e "${YELLOW}Instructions:${NC}"
echo "1. Enter the password for hi@astraverify.com"
echo "2. The password will be stored securely in GCP Secret Manager"
echo "3. The secret will be accessible by the Cloud Run service"
echo ""

echo -e "${YELLOW}Secret Details:${NC}"
echo "Secret Name: astraverify-email-password"
echo "Project: astraverify"
echo ""

# Check if secret exists
if gcloud secrets describe astraverify-email-password >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Secret 'astraverify-email-password' exists${NC}"
else
    echo -e "${RED}❌ Secret 'astraverify-email-password' not found${NC}"
    echo "Creating secret..."
    gcloud secrets create astraverify-email-password --replication-policy="automatic"
fi

echo ""
echo -e "${YELLOW}Enter the password for hi@astraverify.com:${NC}"
echo -e "${BLUE}(The password will be hidden when you type)${NC}"
echo ""

# Read password securely
read -s -p "Password: " EMAIL_PASSWORD
echo ""

if [ -z "$EMAIL_PASSWORD" ]; then
    echo -e "${RED}❌ Password cannot be empty${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Adding password to GCP Secret Manager...${NC}"

# Add the password to the secret
echo "$EMAIL_PASSWORD" | gcloud secrets versions add astraverify-email-password --data-file=-

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Password added to GCP Secret Manager successfully!${NC}"
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "1. Grant access to Cloud Run service"
    echo "2. Update deployment to use the secret"
    echo "3. Deploy the updated application"
    echo ""
    echo -e "${BLUE}Run these commands:${NC}"
    echo "gcloud secrets add-iam-policy-binding astraverify-email-password \\"
    echo "  --member='serviceAccount:astraverify@astraverify.iam.gserviceaccount.com' \\"
    echo "  --role='roles/secretmanager.secretAccessor'"
    echo ""
    echo "./deploy/deploy_production.sh (for production) or ./deploy/deploy_staging.sh (for staging)"
else
    echo -e "${RED}❌ Failed to add password to secret${NC}"
    exit 1
fi
