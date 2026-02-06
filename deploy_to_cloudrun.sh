#!/bin/bash
# Deploy Environmental Monitoring System to Google Cloud Run

# Configuration
PROJECT_ID="crafty-hook-483415-b3"
REGION="us-central1"
SERVICE_NAME="env-monitor-api"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Deploying Environmental Monitoring System to Cloud Run"
echo "   Project: $PROJECT_ID"
echo "   Region: $REGION"
echo "   Service: $SERVICE_NAME"
echo ""

# Enable required APIs
echo "📦 Enabling Cloud Run API..."
gcloud services enable run.googleapis.com --project=$PROJECT_ID
gcloud services enable containerregistry.googleapis.com --project=$PROJECT_ID

# Build and push container
echo "🔨 Building container image..."
gcloud builds submit --tag $IMAGE_NAME --project=$PROJECT_ID -f Dockerfile.cloudrun .

# Deploy to Cloud Run
echo "☁️ Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --project $PROJECT_ID

# Get the service URL
echo ""
echo "✅ Deployment complete!"
echo ""
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --project $PROJECT_ID --format 'value(status.url)')
echo "🌐 Your API is live at: $SERVICE_URL"
echo ""
echo "Try these endpoints:"
echo "  - ${SERVICE_URL}/"
echo "  - ${SERVICE_URL}/docs"
echo "  - ${SERVICE_URL}/api/v1/sensors"
echo "  - ${SERVICE_URL}/api/v1/collaboration/status"
