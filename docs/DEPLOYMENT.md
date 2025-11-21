# Deployment Guide

## Prerequisites
- Google Cloud Project
- gcloud CLI installed
- Docker installed

## First-Time Setup

### 1. Enable Required APIs
```bash
gcloud services enable \
  run.googleapis.com \
  containerregistry.googleapis.com \
  secretmanager.googleapis.com \
  storage-api.googleapis.com
```

### 2. Create Secrets
```bash
echo -n "YOUR_GEMINI_KEY" | gcloud secrets create gemini-api-key --data-file=-
echo -n "YOUR_NANOBANANA_KEY" | gcloud secrets create nanobanana-api-key --data-file=-
```

### 3. Build and Deploy
```bash
# Build locally
docker build -t gcr.io/PROJECT_ID/shortfactory-backend .

# Push to registry
docker push gcr.io/PROJECT_ID/shortfactory-backend

# Deploy
gcloud run deploy shortfactory-backend \
  --image gcr.io/PROJECT_ID/shortfactory-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## Monitoring

- **Logs**: https://console.cloud.google.com/logs
- **Metrics**: https://console.cloud.google.com/monitoring
- **Cloud Run Dashboard**: https://console.cloud.google.com/run

## Local Development

To run the application locally using Docker Compose:

```bash
docker-compose up --build
```

The API will be available at `http://localhost:8000`.
Health check: `http://localhost:8000/health`
Docs: `http://localhost:8000/docs`
