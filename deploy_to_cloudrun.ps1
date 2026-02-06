# Deploy Environmental Monitoring System to Google Cloud Run (PowerShell)

# Configuration
$PROJECT_ID = "crafty-hook-483415-b3"
$REGION = "us-central1"
$SERVICE_NAME = "env-monitor-api"
$IMAGE_NAME = "gcr.io/$PROJECT_ID/$SERVICE_NAME"

Write-Host "🚀 Deploying Environmental Monitoring System to Cloud Run" -ForegroundColor Cyan
Write-Host "   Project: $PROJECT_ID"
Write-Host "   Region: $REGION"
Write-Host "   Service: $SERVICE_NAME"
Write-Host ""

# Enable required APIs
Write-Host "📦 Enabling Cloud Run API..." -ForegroundColor Yellow
gcloud services enable run.googleapis.com --project=$PROJECT_ID
gcloud services enable containerregistry.googleapis.com --project=$PROJECT_ID
gcloud services enable cloudbuild.googleapis.com --project=$PROJECT_ID

# Build and push container
Write-Host "🔨 Building container image..." -ForegroundColor Yellow
gcloud builds submit --tag $IMAGE_NAME --project=$PROJECT_ID -f Dockerfile.cloudrun .

# Deploy to Cloud Run
Write-Host "☁️ Deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy $SERVICE_NAME `
    --image $IMAGE_NAME `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --memory 1Gi `
    --cpu 1 `
    --min-instances 0 `
    --max-instances 10 `
    --project $PROJECT_ID

# Get the service URL
Write-Host ""
Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host ""
$SERVICE_URL = gcloud run services describe $SERVICE_NAME --region $REGION --project $PROJECT_ID --format 'value(status.url)'
Write-Host "🌐 Your API is live at: $SERVICE_URL" -ForegroundColor Cyan
Write-Host ""
Write-Host "Try these endpoints:"
Write-Host "  - $SERVICE_URL/"
Write-Host "  - $SERVICE_URL/docs"
Write-Host "  - $SERVICE_URL/api/v1/sensors"
Write-Host "  - $SERVICE_URL/api/v1/collaboration/status"
