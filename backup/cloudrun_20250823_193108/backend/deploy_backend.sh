#!/bin/bash

# Exit on error
set -e

# Configuration (update these)
PROJECT_ID="your-gcp-project-id"
SERVICE_NAME="astraverify-backend"
REGION="us-central1"

echo "🔧 Setting GCP project..."
gcloud config set project $PROJECT_ID

echo "🐳 Building Docker image and submitting to Cloud Build..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME .

echo "🚀 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME   --image gcr.io/$PROJECT_ID/$SERVICE_NAME   --platform managed   --region $REGION   --allow-unauthenticated

echo "✅ Backend deployed successfully to Cloud Run!"
