# Environmental Monitoring System - Deployment Guide

## Prerequisites

- Google Cloud account with billing enabled
- `gcloud` CLI installed and authenticated
- Docker installed (for local testing)
- Python 3.11+

## Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Application
ENVIRONMENT=production
LOG_LEVEL=INFO
LOG_FORMAT=json

# Security (REQUIRED - change these!)
API_KEY=your-secure-api-key-here
ADMIN_API_KEY=your-secure-admin-key-here
CORS_ORIGINS=https://your-dashboard-url.run.app

# Rate Limiting
RATE_LIMIT_CALLS=100
RATE_LIMIT_PERIOD=60

# External API Keys (optional - for full functionality)
OPENAQ_API_KEY=your-openaq-key
OPENWEATHERMAP_API_KEY=your-owm-key
```

## Local Development

### Backend

```bash
cd environmental_monitoring/backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd environmental_monitoring/frontend

# Install dependencies
pip install -r requirements.txt

# Run development server
python app.py
```

Access:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Dashboard: http://localhost:8050

## Google Cloud Run Deployment

### 1. Set Project Variables

```bash
# Set your project ID
$PROJECT_ID = "your-gcp-project-id"
$REGION = "us-central1"

# Configure gcloud
gcloud config set project $PROJECT_ID
gcloud config set run/region $REGION
```

### 2. Deploy Backend API

```bash
cd environmental_monitoring/backend

# Build and deploy
gcloud builds submit --tag gcr.io/$PROJECT_ID/env-monitor-api

gcloud run deploy env-monitor-api `
    --image gcr.io/$PROJECT_ID/env-monitor-api `
    --platform managed `
    --allow-unauthenticated `
    --set-env-vars "ENVIRONMENT=production,LOG_FORMAT=json" `
    --set-secrets "API_KEY=api-key:latest,ADMIN_API_KEY=admin-api-key:latest"
```

### 3. Deploy Frontend Dashboard

```bash
cd environmental_monitoring/frontend

# Build and deploy
gcloud builds submit --tag gcr.io/$PROJECT_ID/env-monitor-dashboard

gcloud run deploy env-monitor-dashboard `
    --image gcr.io/$PROJECT_ID/env-monitor-dashboard `
    --platform managed `
    --allow-unauthenticated `
    --set-env-vars "API_URL=https://env-monitor-api-xxx.run.app"
```

### 4. Update CORS Origins

After deploying the dashboard, update the API's CORS settings:

```bash
gcloud run services update env-monitor-api `
    --set-env-vars "CORS_ORIGINS=https://env-monitor-dashboard-xxx.run.app"
```

## Secret Management

Store sensitive values in Google Secret Manager:

```bash
# Create secrets
echo -n "your-api-key" | gcloud secrets create api-key --data-file=-
echo -n "your-admin-key" | gcloud secrets create admin-api-key --data-file=-

# Grant access to Cloud Run service account
gcloud secrets add-iam-policy-binding api-key `
    --member="serviceAccount:xxx@xxx.iam.gserviceaccount.com" `
    --role="roles/secretmanager.secretAccessor"
```

## Health Checks

Cloud Run uses these endpoints for health checking:

| Endpoint | Purpose | Expected Response |
|----------|---------|-------------------|
| `/ok` | Liveness probe | `{"status": "ok"}` |
| `/ready` | Readiness probe | `{"status": "ready"}` or 503 |
| `/health` | Detailed health | Full status with dependencies |

Configure in Cloud Run:

```bash
gcloud run services update env-monitor-api `
    --startup-cpu-boost `
    --startup-probe-path=/ok `
    --startup-probe-initial-delay=5s `
    --startup-probe-timeout=2s `
    --startup-probe-period=5s `
    --liveness-probe-path=/ok `
    --liveness-probe-initial-delay=10s
```

## Monitoring & Logging

### View Logs

```bash
# Stream logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=env-monitor-api" `
    --format="table(timestamp,severity,jsonPayload.message)" `
    --freshness=1h

# Error logs only
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" --freshness=5m
```

### Set Up Alerts

1. Go to Cloud Monitoring in GCP Console
2. Create alerting policy for:
   - Error rate > 5%
   - Latency p95 > 2s
   - Instance count changes

## Scaling Configuration

```bash
gcloud run services update env-monitor-api `
    --min-instances=1 `
    --max-instances=10 `
    --memory=512Mi `
    --cpu=1 `
    --concurrency=100
```

## Troubleshooting

### Container Fails to Start

1. Check PORT environment variable (Cloud Run sets PORT=8080)
2. Verify Dockerfile uses `port=int(os.environ.get("PORT", 8000))`
3. Check logs: `gcloud logging read "severity>=ERROR" --freshness=5m`

### Rate Limiting Issues

1. Check client IP extraction works behind Cloud Run proxy
2. Adjust `RATE_LIMIT_CALLS` and `RATE_LIMIT_PERIOD` as needed

### Database Connection Issues

1. SQLite works for development but consider PostgreSQL for production
2. For Cloud SQL, add `--add-cloudsql-instances` flag

### CORS Errors

1. Verify `CORS_ORIGINS` includes the dashboard URL
2. Check for trailing slashes (should not have them)
3. Redeploy API after updating CORS settings

## Production Checklist

- [ ] Change default API keys
- [ ] Set ENVIRONMENT=production
- [ ] Enable LOG_FORMAT=json
- [ ] Restrict CORS_ORIGINS to dashboard URL only
- [ ] Set up Secret Manager for API keys
- [ ] Configure health check probes
- [ ] Set up monitoring alerts
- [ ] Review rate limiting settings
- [ ] Enable Cloud Armor for DDoS protection (optional)
- [ ] Set up Cloud CDN for static assets (optional)
