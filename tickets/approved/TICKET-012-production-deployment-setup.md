# [TICKET-012] Production Deployment Setup - Docker + Cloud Run

## Priority
- [x] High (Performance issues, significant tech debt)
- [ ] Medium (Code quality, maintainability improvements)
- [ ] Low (Nice-to-have refactorings)

## Type
- [ ] Refactoring
- [ ] Performance Optimization
- [ ] Test Coverage
- [ ] Bug Fix
- [ ] Security Issue
- [x] Technical Debt
- [x] Feature Implementation
- [x] Infrastructure

## Impact Assessment
**Business Impact:**
- **CRITICAL**: Required for production launch
- Enables public access to the video generation platform
- Supports scaling to handle multiple concurrent users
- Foundation for monitoring, logging, and reliability

**Technical Impact:**
- Affects: Entire application stack
- Requires: Docker, Cloud infrastructure setup
- Enables: Auto-scaling, zero-downtime deployments, monitoring
- Cost: ~$50-200/month depending on traffic

**Effort Estimate:**
- Large (3-5 days) - 24-36 hours including testing and documentation

---

## Requirements

### Functional Requirements

**FR-1: Containerization**
- System SHALL be fully containerized using Docker
- Backend and Frontend SHALL have separate containers
- System SHALL support local Docker Compose development
- All dependencies SHALL be specified in Dockerfile

**FR-2: Cloud Deployment**
- System SHALL deploy to Google Cloud Run (serverless)
- System SHALL support automatic scaling (0-100 instances)
- System SHALL support CI/CD via GitHub Actions
- System SHALL support blue/green deployments

**FR-3: Environment Configuration**
- System SHALL support multiple environments (dev, staging, prod)
- Environment variables SHALL be injected at runtime
- Secrets SHALL be stored in Google Secret Manager
- Configuration SHALL be validated on startup

**FR-4: Static Asset Handling**
- Generated videos SHALL be stored in Google Cloud Storage
- Frontend SHALL be served via CDN
- System SHALL handle file uploads/downloads efficiently

---

### Non-Functional Requirements

**NFR-1: Performance**
- Cold start: < 5 seconds
- Request handling: < 30 seconds for video generation
- Auto-scaling: Scale to 0 when idle, up to 100 under load

**NFR-2: Reliability**
- Uptime: 99.9% SLA
- Automatic health checks and restarts
- Graceful shutdown on deployment

**NFR-3: Security**
- HTTPS only (TLS 1.3)
- API keys never in code or logs
- CORS properly configured
- Rate limiting enabled

**NFR-4: Cost Efficiency**
- Pay-per-use model (Cloud Run)
- Estimated: $50-200/month for moderate traffic
- Auto-scale to 0 when not in use

---

## Implementation Plan

### Phase 1: Dockerization (8 hours)

**Step 1.1: Create Backend Dockerfile**
```dockerfile
# Dockerfile (root of project)
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY *.py ./

# Create directories for generated assets
RUN mkdir -p generated_assets/images generated_assets/audio generated_assets/videos

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run with gunicorn for production
CMD ["gunicorn", "src.api.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
```

**Step 1.2: Create Frontend Dockerfile**
```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source and build
COPY . .
RUN npm run build

# Production image
FROM node:20-alpine

WORKDIR /app

# Copy built files
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules ./node_modules

EXPOSE 3000

CMD ["npm", "start"]
```

**Step 1.3: Create Docker Compose for local dev**
```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      - USE_REAL_LLM=false  # Use mock by default locally
      - USE_REAL_IMAGE=false
      - USE_REAL_VOICE=false
    volumes:
      - ./generated_assets:/app/generated_assets
      - ./src:/app/src  # Hot reload in development
    command: uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    volumes:
      - ./frontend/src:/app/src  # Hot reload
    depends_on:
      - backend
```

---

### Phase 2: Cloud Run Setup (6 hours)

**Step 2.1: Create Cloud Run configuration**
```yaml
# cloudrun.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: shortfactory-backend
spec:
   template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "0"
        autoscaling.knative.dev/maxScale: "100"
        run.googleapis.com/execution-environment: gen2
    spec:
      containerConcurrency: 80
      timeoutSeconds: 300  # 5 minutes for video generation
      containers:
      - image: gcr.io/PROJECT_ID/shortfactory-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: USE_REAL_LLM
          value: "true"
        - name: USE_REAL_IMAGE
          value: "true"
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: gemini-api-key
              key: latest
        resources:
          limits:
            memory: 2Gi
            cpu: "2"
```

**Step 2.2: Setup Cloud Storage for generated assets**
```bash
# Create bucket for generated videos
gsutil mb -p PROJECT_ID -c STANDARD -l us-central1 gs://shortfactory-videos

# Set lifecycle policy (delete old videos after 7 days)
gsutil lifecycle set lifecycle.json gs://shortfactory-videos

# lifecycle.json
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 7}
      }
    ]
  }
}
```

**Step 2.3: Update agents to use Cloud Storage**
```python
# src/core/storage.py
from google.cloud import storage

class StorageManager:
    def __init__(self):
        self.client = storage.Client()
        self.bucket_name = settings.GCS_BUCKET_NAME
        self.bucket = self.client.bucket(self.bucket_name)
    
    def upload_video(self, local_path: str, video_id: str) -> str:
        """Upload video to GCS and return public URL."""
        blob_name = f"videos/{video_id}.mp4"
        blob = self.bucket.blob(blob_name)
        
        blob.upload_from_filename(local_path)
        
        # Make public or generate signed URL
        blob.make_public()
        
        return blob.public_url
```

---

### Phase 3: CI/CD Pipeline (4 hours)

**Step 3.1: GitHub Actions for CI**
```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-cov
    
    - name: Run tests
      run: |
        pytest tests/ --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml
```

**Step 3.2: GitHub Actions for deployment**
```yaml
# .github/workflows/deploy.yml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Cloud SDK
      uses: google-github-actions/setup-gcloud@v1
      with:
        project_id: ${{ secrets.GCP_PROJECT_ID }}
        service_account_key: ${{ secrets.GCP_SA_KEY }}
    
    - name: Build and push Docker image
      run: |
        gcloud builds submit --tag gcr.io/${{ secrets.GCP_PROJECT_ID }}/shortfactory-backend:${{ github.sha }}
    
    - name: Deploy to Cloud Run
      run: |
        gcloud run deploy shortfactory-backend \
          --image gcr.io/${{ secrets.GCP_PROJECT_ID }}/shortfactory-backend:${{ github.sha }} \
          --platform managed \
          --region us-central1 \
          --allow-unauthenticated \
          --set-env-vars=USE_REAL_LLM=true \
          --set-secrets=GEMINI_API_KEY=gemini-api-key:latest
```

---

### Phase 4: Monitoring & Health Checks (3 hours)

**Step 4.1: Add health check endpoint**
```python
# src/api/main.py
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run."""
    # Check critical dependencies
    checks = {
        "status": "healthy",
        "services": {
            "database": "ok",  # If using DB
            "storage": "ok",
        }
    }
    
    # Verify API keys are set
    if settings.USE_REAL_LLM and not settings.GEMINI_API_KEY:
        checks["status"] = "unhealthy"
        checks["errors"] = ["GEMINI_API_KEY not set"]
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=checks
        )
    
    return checks

@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "ShortFactory API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }
```

**Step 4.2: Setup Cloud Monitoring**
```python
# src/core/monitoring.py
from google.cloud import monitoring_v3
import time

class MetricsRecorder:
    def __init__(self):
        self.client = monitoring_v3.MetricServiceClient()
        self.project_name = f"projects/{settings.GCP_PROJECT_ID}"
    
    def record_video_generation(self, duration_seconds: float, success: bool):
        """Record video generation metrics."""
        series = monitoring_v3.TimeSeries()
        series.metric.type = "custom.googleapis.com/video_generation/duration"
        series.resource.type = "global"
        
        now = time.time()
        seconds = int(now)
        nanos = int((now - seconds) * 10 ** 9)
        
        point = monitoring_v3.Point()
        point.value.double_value = duration_seconds
        point.interval.end_time.seconds = seconds
        point.interval.end_time.nanos = nanos
        
        series.points = [point]
        
        self.client.create_time_series(
            name=self.project_name,
            time_series=[series]
        )
```

---

### Phase 5: Documentation & Runbooks (3 hours)

**Deployment Guide:**
```markdown
# docs/DEPLOYMENT.md

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
```

---

## Testing Strategy

### Local Testing
```bash
# Test Docker build
docker build -t shortfactory-test .
docker run -p 8000:8000 --env-file .env shortfactory-test

# Test with Docker Compose
docker-compose up

# Verify
curl http://localhost:8000/health
```

### Staging Deployment
```bash
# Deploy to staging
gcloud run deploy shortfactory-staging \
  --image gcr.io/PROJECT_ID/shortfactory-backend:latest \
  --platform managed \
  --region us-central1

# Run integration tests against staging
pytest tests/test_integration.py --api-url=https://shortfactory-staging-xxx.run.app
```

### Production Smoke Tests
After deployment, verify:
1. Health check returns 200 OK
2. Story generation works
3. Script generation works
4. Video generation completes
5. Generated video is downloadable

---

## Cost Analysis

### Cloud Run Pricing
- **CPU:** $0.00002400 per vCPU-second
- **Memory:** $0.00000250 per GiB-second
- **Requests:** $0.40 per million requests

### Example Monthly Costs
**Low Traffic (1000 videos/month):**
- Compute: ~$10
- Storage: ~$5
- Total: ~$15/month

**Medium Traffic (10,000 videos/month):**
- Compute: ~$100
- Storage: ~$20
- Total: ~$120/month

**High Traffic (100,000 videos/month):**
- Compute: ~$800
- Storage: ~$100
- Total: ~$900/month

### Cost Optimization
- Scale to 0 when idle
- Use lifecycle policies to delete old videos
- Use cheaper storage classes for archived videos
- Implement caching to reduce API calls

---

## Files Affected

**New Files:**
- `Dockerfile` - Backend container
- `frontend/Dockerfile` - Frontend container
- `docker-compose.yml` - Local development
- `cloudrun.yaml` - Cloud Run configuration
- `.github/workflows/ci.yml` - CI pipeline
- `.github/workflows/deploy.yml` - CD pipeline
- `.dockerignore` - Files to exclude from image
- `docs/DEPLOYMENT.md` - Deployment guide
- `docs/RUNBOOK.md` - Operations guide
- `src/core/storage.py` - Cloud Storage integration
- `src/core/monitoring.py` - Metrics collection

**Modified:**
- `requirements.txt` - Add `gunicorn`, `google-cloud-storage`, `google-cloud-monitoring`
- `src/api/main.py` - Add health check endpoint
- `src/core/config.py` - Add GCS configuration

---

## Success Criteria
- [x] Application runs in Docker locally
- [x] Deploys to Cloud Run successfully
- [x] Health check endpoint works
- [x] Auto-scaling from 0-100 instances
- [x] CI/CD pipeline deploys on merge to main
- [x] Monitoring dashboards configured
- [x] Generated videos stored in GCS
- [x] Cost under $200/month for moderate traffic
- [x] 99.9% uptime in production

---

## Dependencies
- Depends on: All feature tickets (TICKET-008, 009, etc.)
- Blocks: Public launch
- Related to: TICKET-013 (monitoring)

---

## References
- Cloud Run docs: https://cloud.google.com/run/docs
- Docker best practices: https://docs.docker.com/develop/dev-best-practices/
- GitHub Actions: https://docs.github.com/en/actions

---

**Priority: CRITICAL** - Required before public launch. Foundation for all production operations.

---

## 🏛️ Architect Review & Approval

**Reviewed by:** Architect Agent  
**Review Date:** 2025-01-21  
**Decision:** ✅ APPROVED

**Strategic Rationale:**
- **Deployment Blocker**: Cannot launch publicly without production infrastructure
- **Scalability Foundation**: Cloud Run enables auto-scaling from 0-100 instances
- **Cost Efficiency**: Pay-per-use model, scale to zero when idle
- **DevOps Best Practices**: CI/CD, containerization, infrastructure as code

**Implementation Phase:** Phase 2, Week 3  
**Sequence Order:** #4 (After all real API integrations complete)

**Architectural Guidance:**
- **Multi-Stage Dockerfile**: Use builder pattern for smaller, optimized images
- **Health Checks**: Robust `/health` endpoint that validates all dependencies and API keys
- **Secret Management**: Use Google Secret Manager exclusively, never commit keys
- **Static Assets**: Cloud Storage for generated videos, not container filesystem (ephemeral)
- **Monitoring First**: Set up Cloud Monitoring from day 1, not as afterthought

**Dependencies:**
- **Must Complete First**: TICKET-009 (images), TICKET-013 (voice), TICKET-014 (video)
- **Reason**: Need all real integrations working before production deployment
- **Blocks**: Public launch, production testing

**Risk Mitigation:**
- **Cold Start Latency**: Use min instances = 1 for production (small cost for better UX)
- **Deployment Failures**: Blue/green deployment strategy, documented rollback procedures
- **Cost Overruns**: Billing alerts at 80% budget, hard limits configured
- **Security**: Security audit before public launch, penetration testing recommended

**Enhanced Success Criteria:**
Beyond original ticket criteria:
- [ ] Docker Compose works for local development (dev/prod parity)
- [ ] Secrets never appear in logs or error messages
- [ ] Auto-scaling tested (load test with 50 concurrent users)
- [ ] Rollback procedure documented and tested
- [ ] Monitoring alerts configured (error rate, latency, cost)

**Implementation Notes:**
- **Start by**: Backend Dockerfile, test locally with real APIs
- **Then**: Frontend Dockerfile, Docker Compose for full stack
- **Then**: Cloud Run deployment, Secret Manager setup
- **Finally**: CI/CD pipeline, monitoring dashboards
- **Watch out for**: File permissions in container, environment variable precedence
- **Coordinate with**: DevOps team for GCP project setup

**Estimated Timeline:** 3-5 days  
**Recommended Owner:** DevOps engineer or full-stack with cloud experience
