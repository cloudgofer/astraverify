#!/bin/bash
# Cloud Run monitoring script
SERVICE_NAME="astraverify-backend"
REGION="us-central1"

if [[ -f .service_url ]]; then
    SERVICE_URL=$(cat .service_url)
    curl -f -s --max-time 10 "$SERVICE_URL/api/health" >/dev/null
    if [[ $? -eq 0 ]]; then
        echo "OK"
    else
        echo "FAILED"
    fi
else
    echo "NO_URL"
fi
