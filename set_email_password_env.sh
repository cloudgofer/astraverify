#!/bin/bash

echo "=========================================="
echo "  Set EMAIL_PASSWORD in Cloud Run"
echo "=========================================="
echo ""

echo "🔍 Current Cloud Run configuration:"
gcloud run services describe astraverify-backend --region=us-central1 --format="value(spec.template.spec.template.spec.containers[0].env[].name)" 2>/dev/null || echo "No environment variables found"

echo ""
echo "📝 Setting EMAIL_PASSWORD environment variable..."

# Get the password from user
echo "Enter the password for hi@astraverify.com:"
read -s EMAIL_PASSWORD

if [ -z "$EMAIL_PASSWORD" ]; then
    echo "❌ Password cannot be empty"
    exit 1
fi

echo ""
echo "🔧 Updating Cloud Run service..."

# Update the Cloud Run service with the environment variable
gcloud run services update astraverify-backend \
    --region=us-central1 \
    --set-env-vars="EMAIL_PASSWORD=$EMAIL_PASSWORD" \
    --quiet

if [ $? -eq 0 ]; then
    echo "✅ EMAIL_PASSWORD environment variable set successfully!"
    echo ""
    echo "🔍 Verifying configuration..."
    gcloud run services describe astraverify-backend --region=us-central1 --format="value(spec.template.spec.template.spec.containers[0].env[].name)" | grep EMAIL_PASSWORD
    if [ $? -eq 0 ]; then
        echo "✅ EMAIL_PASSWORD environment variable is configured"
    else
        echo "❌ EMAIL_PASSWORD environment variable not found"
    fi
else
    echo "❌ Failed to set EMAIL_PASSWORD environment variable"
    exit 1
fi

echo ""
echo "🚀 Testing email configuration..."
sleep 5
curl -X GET "https://astraverify-backend-ml2mhibdvq-uc.a.run.app/api/test-email" | jq .

echo ""
echo "✅ Setup complete! The email configuration should now work."
