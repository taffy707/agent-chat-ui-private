# Production Deployment Guide

## Overview

This guide covers deploying your FastAPI document management system to production using:

- **Docker** for containerization
- **Google Cloud Run** for serverless hosting
- **Cloud SQL** for PostgreSQL database
- **Google Cloud Storage** for document storage (already configured)

---

## Option 1: Docker Containerization ⭐ RECOMMENDED

### Step 1: Create Dockerfile

Create `Dockerfile`:

```dockerfile
# Dockerfile

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Step 2: Create .dockerignore

Create `.dockerignore`:

```
# .dockerignore

__pycache__
*.pyc
*.pyo
*.pyd
.Python
venv/
env/
.env
.git
.gitignore
*.md
*.log
.DS_Store
test_*.txt
server.log
*.pdf
*.docx
```

### Step 3: Build Docker Image

```bash
# Build the image
docker build -t document-api:latest .

# Test locally
docker run -p 8000:8000 \
  -e GCP_PROJECT_ID=metatask-461115 \
  -e VERTEX_AI_DATA_STORE_ID=metatask_1761751621392 \
  -e VERTEX_AI_LOCATION=global \
  -e GCS_BUCKET_NAME=metatask-documents-upload-bucket \
  -e POSTGRES_HOST=host.docker.internal \
  -e POSTGRES_PORT=5432 \
  -e POSTGRES_USER=your_user \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=vertex_ai_documents \
  document-api:latest
```

### Step 4: Docker Compose (For Local Development)

Create `docker-compose.yml`:

```yaml
# docker-compose.yml

version: "3.8"

services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: vertex_ai_documents
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GCP_PROJECT_ID=metatask-461115
      - VERTEX_AI_DATA_STORE_ID=metatask_1761751621392
      - VERTEX_AI_LOCATION=global
      - GCS_BUCKET_NAME=metatask-documents-upload-bucket
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=vertex_ai_documents
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./google-credentials.json:/app/google-credentials.json:ro
    env_file:
      - .env

volumes:
  postgres_data:
```

Run with:

```bash
docker-compose up -d
```

---

## Option 2: Deploy to Google Cloud Run

### Step 1: Install Google Cloud SDK

```bash
# Install gcloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Login
gcloud auth login

# Set project
gcloud config set project metatask-461115
```

### Step 2: Set Up Cloud SQL (PostgreSQL)

```bash
# Create Cloud SQL instance
gcloud sql instances create document-db \
    --database-version=POSTGRES_14 \
    --tier=db-f1-micro \
    --region=us-central1 \
    --root-password=YOUR_SECURE_PASSWORD

# Create database
gcloud sql databases create vertex_ai_documents --instance=document-db

# Get connection name
gcloud sql instances describe document-db --format="value(connectionName)"
# Output: metatask-461115:us-central1:document-db
```

### Step 3: Build and Push to Container Registry

```bash
# Enable required APIs
gcloud services enable \
    containerregistry.googleapis.com \
    run.googleapis.com \
    sqladmin.googleapis.com

# Build and push image
gcloud builds submit --tag gcr.io/metatask-461115/document-api

# Or using Docker
docker build -t gcr.io/metatask-461115/document-api .
docker push gcr.io/metatask-461115/document-api
```

### Step 4: Deploy to Cloud Run

```bash
# Deploy with Cloud SQL connection
gcloud run deploy document-api \
    --image gcr.io/metatask-461115/document-api \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --add-cloudsql-instances metatask-461115:us-central1:document-db \
    --set-env-vars "GCP_PROJECT_ID=metatask-461115" \
    --set-env-vars "VERTEX_AI_DATA_STORE_ID=metatask_1761751621392" \
    --set-env-vars "VERTEX_AI_LOCATION=global" \
    --set-env-vars "GCS_BUCKET_NAME=metatask-documents-upload-bucket" \
    --set-env-vars "POSTGRES_HOST=/cloudsql/metatask-461115:us-central1:document-db" \
    --set-env-vars "POSTGRES_PORT=5432" \
    --set-env-vars "POSTGRES_USER=postgres" \
    --set-env-vars "POSTGRES_PASSWORD=YOUR_SECURE_PASSWORD" \
    --set-env-vars "POSTGRES_DB=vertex_ai_documents" \
    --memory 512Mi \
    --timeout 300 \
    --max-instances 10
```

### Step 5: Update Database Connection for Cloud SQL

Update `database.py` to handle both local and Cloud SQL connections:

```python
# database.py - Update connect method

async def connect(self):
    """Initialize database connection pool."""
    # Check if using Unix socket (Cloud SQL)
    if settings.POSTGRES_HOST.startswith('/cloudsql/'):
        # Cloud SQL Unix socket connection
        self.pool = await asyncpg.create_pool(
            host=settings.POSTGRES_HOST,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB,
            min_size=1,
            max_size=5,
            command_timeout=60,
        )
    else:
        # Standard TCP connection
        self.pool = await asyncpg.create_pool(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB,
            min_size=2,
            max_size=10,
            command_timeout=60,
        )
    logger.info(f"✅ Database connection pool established")
```

### Step 6: Get Service URL

```bash
# Get the deployed URL
gcloud run services describe document-api \
    --region us-central1 \
    --format "value(status.url)"

# Output: https://document-api-xxxxx-uc.a.run.app
```

---

## Option 3: Deploy to AWS (ECS + RDS)

### Step 1: Create RDS PostgreSQL Instance

```bash
# Using AWS CLI
aws rds create-db-instance \
    --db-instance-identifier document-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --engine-version 14.7 \
    --master-username postgres \
    --master-user-password YOUR_SECURE_PASSWORD \
    --allocated-storage 20 \
    --vpc-security-group-ids sg-xxxxx \
    --db-subnet-group-name your-subnet-group \
    --publicly-accessible
```

### Step 2: Push to Amazon ECR

```bash
# Create ECR repository
aws ecr create-repository --repository-name document-api

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin \
    123456789012.dkr.ecr.us-east-1.amazonaws.com

# Build and push
docker build -t document-api .
docker tag document-api:latest \
    123456789012.dkr.ecr.us-east-1.amazonaws.com/document-api:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/document-api:latest
```

### Step 3: Deploy to ECS Fargate

Create `task-definition.json`:

```json
{
  "family": "document-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "document-api",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/document-api:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        { "name": "GCP_PROJECT_ID", "value": "metatask-461115" },
        {
          "name": "VERTEX_AI_DATA_STORE_ID",
          "value": "metatask_1761751621392"
        },
        { "name": "POSTGRES_HOST", "value": "your-rds-endpoint.amazonaws.com" },
        { "name": "POSTGRES_DB", "value": "vertex_ai_documents" }
      ],
      "secrets": [
        {
          "name": "POSTGRES_PASSWORD",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:db-password"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/document-api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

---

## Environment Variables for Production

Create `.env.production`:

```bash
# .env.production

# Google Cloud
GCP_PROJECT_ID=metatask-461115
VERTEX_AI_DATA_STORE_ID=metatask_1761751621392
VERTEX_AI_LOCATION=global
GCS_BUCKET_NAME=metatask-documents-upload-bucket

# Database (use Cloud SQL or RDS endpoint)
POSTGRES_HOST=your-db-host
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=SECURE_PASSWORD_HERE
POSTGRES_DB=vertex_ai_documents

# API Settings
API_TITLE=Document Upload API
API_VERSION=1.0.0

# Deletion Queue
DELETION_QUEUE_WORKER_INTERVAL=60
DELETION_QUEUE_MAX_ATTEMPTS=10
DELETION_QUEUE_INITIAL_DELAY=120
```

---

## Security Best Practices

### 1. Use Secret Manager

**Google Cloud Secret Manager:**

```bash
# Store secrets
echo -n "your-db-password" | \
    gcloud secrets create db-password --data-file=-

# Grant access to Cloud Run
gcloud secrets add-iam-policy-binding db-password \
    --member="serviceAccount:PROJECT_ID-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# Use in Cloud Run
gcloud run deploy document-api \
    --set-secrets="POSTGRES_PASSWORD=db-password:latest"
```

### 2. Enable HTTPS Only

Cloud Run automatically provides HTTPS. For custom domains:

```bash
# Map custom domain
gcloud run domain-mappings create \
    --service document-api \
    --domain api.yourdomain.com \
    --region us-central1
```

### 3. Set Up Authentication

Add API key authentication in `main.py`:

```python
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key"
        )
    return api_key

# Protect endpoints
@app.post("/upload", dependencies=[Depends(verify_api_key)])
async def upload_documents(...):
    ...
```

### 4. Rate Limiting

Add rate limiting middleware:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/upload")
@limiter.limit("10/minute")
async def upload_documents(request: Request, ...):
    ...
```

---

## Monitoring & Logging

### Google Cloud Logging

```bash
# View logs
gcloud run logs read document-api \
    --region us-central1 \
    --limit 50

# Stream logs
gcloud run logs tail document-api \
    --region us-central1
```

### Add Structured Logging

Update `main.py`:

```python
import logging
import json

# Configure JSON logging for Cloud Logging
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }
        return json.dumps(log_obj)

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logging.getLogger().addHandler(handler)
```

### Set Up Alerting

```bash
# Create alert for high error rate
gcloud alpha monitoring policies create \
    --notification-channels=CHANNEL_ID \
    --display-name="High Error Rate" \
    --condition-display-name="Error rate > 5%" \
    --condition-threshold-value=0.05
```

---

## Performance Optimization

### 1. Add Health Check Endpoint

Already exists at `/health` - configure Cloud Run to use it:

```bash
gcloud run services update document-api \
    --region us-central1 \
    --startup-cpu-boost
```

### 2. Connection Pooling

Already configured in `database.py` with:

- Min pool size: 2
- Max pool size: 10
- Command timeout: 60s

### 3. Enable CDN (Optional)

For static assets, enable Cloud CDN:

```bash
gcloud compute backend-services update document-api \
    --enable-cdn
```

---

## CI/CD Pipeline

### GitHub Actions Example

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
        with:
          project_id: metatask-461115
          service_account_key: ${{ secrets.GCP_SA_KEY }}

      - name: Build and push image
        run: |
          gcloud builds submit --tag gcr.io/metatask-461115/document-api

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy document-api \
            --image gcr.io/metatask-461115/document-api \
            --region us-central1 \
            --platform managed
```

---

## Cost Optimization

### Cloud Run Pricing

**Free Tier:**

- 2 million requests/month
- 360,000 GB-seconds/month
- 180,000 vCPU-seconds/month

**After Free Tier:**

- $0.00002400/request
- $0.00001800/GB-second
- $0.00002400/vCPU-second

### Cloud SQL Pricing

**db-f1-micro (development):**

- ~$7/month

**db-custom-1-3840 (production):**

- ~$50/month

### Recommendations

1. ✅ Use Cloud Run (serverless, scales to zero)
2. ✅ Use smallest Cloud SQL instance for dev
3. ✅ Scale up Cloud SQL only when needed
4. ✅ Set max instances on Cloud Run
5. ✅ Enable deletion queue to batch operations

**Estimated Monthly Cost:**

- Cloud Run: $0-20 (depending on traffic)
- Cloud SQL: $7-50 (depending on size)
- Cloud Storage: Already configured
- **Total: ~$10-70/month**

---

## Checklist for Production

- [ ] Docker image builds successfully
- [ ] Environment variables configured
- [ ] Database migrations run
- [ ] CORS configured for frontend domain
- [ ] HTTPS enabled
- [ ] Secrets stored in Secret Manager
- [ ] Health checks passing
- [ ] Logging configured
- [ ] Monitoring/alerts set up
- [ ] Rate limiting enabled
- [ ] API authentication added
- [ ] Backup strategy for database
- [ ] CI/CD pipeline configured

Your API is ready for production deployment! 🚀
