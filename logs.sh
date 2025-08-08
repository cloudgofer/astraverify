#!/bin/bash

echo "📊 AstraVerify Logs Tailer"
echo "=========================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "Choose log type:"
echo "1) All logs (backend + frontend)"
echo "2) Backend logs only"
echo "3) Frontend logs only"
echo "4) Error logs only"
echo "5) Email/SMTP logs only"
echo ""

read -p "Enter choice (1-5): " choice

case $choice in
    1)
        echo "📡 Tailing all logs..."
        gcloud beta logging tail "resource.type=cloud_run_revision AND (resource.labels.service_name=astraverify-backend OR resource.labels.service_name=astraverify-frontend)" --format="table(timestamp,severity,resource.labels.service_name,textPayload)"
        ;;
    2)
        echo "🔧 Tailing backend logs..."
        gcloud beta logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=astraverify-backend" --format="table(timestamp,severity,textPayload)"
        ;;
    3)
        echo "🎨 Tailing frontend logs..."
        gcloud beta logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=astraverify-frontend" --format="table(timestamp,severity,textPayload)"
        ;;
    4)
        echo "❌ Tailing error logs..."
        gcloud beta logging tail "resource.type=cloud_run_revision AND (resource.labels.service_name=astraverify-backend OR resource.labels.service_name=astraverify-frontend) AND severity>=ERROR" --format="table(timestamp,severity,resource.labels.service_name,textPayload)"
        ;;
    5)
        echo "📧 Tailing email/SMTP logs..."
        gcloud beta logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=astraverify-backend AND (textPayload:email OR textPayload:smtp OR textPayload:SMTP)" --format="table(timestamp,severity,textPayload)"
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac
