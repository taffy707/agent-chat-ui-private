# Docker and Cloud Deployment Guide with Authentication

This guide covers running the Document API with authentication using Docker locally, then deploying to Google Cloud Run.

## 📋 What's Been Updated

✅ **Docker Configuration:**

- Added Supabase authentication environment variables to `docker-compose.yml`
- Created `.env.docker` with Supabase credentials
- Updated for authentication support

✅ **Frontend Configuration:**

- Updated `.env` to point to local Docker (`http://localhost:8000`)
- Cloud URL saved as comment for easy switching

✅ **Cloud Deployment:**

- Created `deploy-cloudrun.sh` script with authentication
- Includes Supabase environment variables in Cloud Run deployment

---

## Part 1: Test with Docker Locally

### Step 1: Verify Files Are Ready

Make sure these files exist in `/document-api/`:

- ✅ `Dockerfile` - Updated with latest code
- ✅ `docker-compose.yml` - Updated with Supabase auth vars
- ✅ `.env` - Your local environment variables
- ✅ `.env.docker` - Docker-specific environment (just created)
- ✅ `requirements.txt` - Includes `supabase>=2.8.0`

### Step 2: Check Docker is Running

```bash
# Check Docker status
docker --version
docker ps

# If Docker isn't running, start Docker Desktop first
```

### Step 3: Build and Start Docker Container

**Option A: Using the convenience script (Recommended)**

```bash
cd document-api

# Start Docker containers
./docker-start.sh
```

**Option B: Using docker-compose directly**

```bash
cd document-api

# Build and start
docker-compose up -d --build

# View logs
docker-compose logs -f api
```

### Step 4: Verify Docker is Running

The script should show:

```
✅ Document API is running!

📍 API URL: http://localhost:8000
📍 API Docs: http://localhost:8000/docs
📍 Health Check: http://localhost:8000/health
```

**Manual verification:**

```bash
# Check container is running
docker ps | grep document-api

# Test health endpoint
curl http://localhost:8000/health

# View logs
docker-compose logs api
```

Expected health response:

```json
{
  "status": "healthy",
  "gcp_project": "metatask-461115",
  "datastore_id": "metatask_1761751621392",
  "bucket": "metatask-documents-bucket"
}
```

### Step 5: Test Authentication

**Get your JWT token** (from frontend after signing in):

```javascript
// In browser console at localhost:3000
const token = JSON.parse(localStorage.getItem("supabase.auth.token"))
  ?.currentSession?.access_token;
console.log("Token:", token);
copy(token); // Copies to clipboard
```

**Test with curl:**

```bash
export TOKEN="your-token-here"

# Test creating a collection
curl -X POST http://localhost:8000/collections \
  -H "Authorization: Bearer $TOKEN" \
  -F "name=Docker Test Collection" \
  -F "description=Testing Docker with auth"

# Test listing collections
curl -X GET http://localhost:8000/collections \
  -H "Authorization: Bearer $TOKEN"
```

Expected: 201 Created for POST, 200 OK for GET with your collections

### Step 6: Test from Frontend

1. Make sure frontend is running: `pnpm dev`
2. Frontend `.env` should have: `NEXT_PUBLIC_DOCUMENT_API_URL=http://localhost:8000`
3. Sign in to the frontend
4. Use the browser console or example component to test API calls

```javascript
// In browser console
const response = await fetch("http://localhost:8000/collections", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${JSON.parse(localStorage.getItem("supabase.auth.token"))?.currentSession?.access_token}`,
  },
  body: (() => {
    const fd = new FormData();
    fd.append("name", "Test from Browser");
    return fd;
  })(),
});
const data = await response.json();
console.log("Created:", data);
```

### Troubleshooting Docker

**Container won't start:**

```bash
# View detailed logs
docker-compose logs api

# Check if port 8000 is already in use
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Stop and restart
docker-compose down
docker-compose up -d --build
```

**Can't connect to PostgreSQL:**

- Ensure PostgreSQL is running on your host machine
- Check `POSTGRES_HOST=host.docker.internal` in docker-compose.yml
- Verify PostgreSQL is accessible from Docker:
  ```bash
  docker-compose exec api psql -h host.docker.internal -U tafadzwabwakura -d vertex_ai_documents
  ```

**Authentication errors:**

- Verify Supabase credentials in `.env.docker`
- Check logs: `docker-compose logs api | grep -i supabase`
- Ensure frontend and backend use same Supabase project

### Stopping Docker

```bash
# Stop containers
docker-compose down

# Or use convenience script
./docker-stop.sh

# Stop and remove volumes (WARNING: Deletes data)
docker-compose down -v
```

---

## Part 2: Deploy to Google Cloud Run

### Prerequisites

1. **Google Cloud SDK installed:**

   ```bash
   gcloud --version
   # If not installed: https://cloud.google.com/sdk/docs/install
   ```

2. **Authenticated with Google Cloud:**

   ```bash
   gcloud auth login
   gcloud config set project metatask-461115
   ```

3. **Supabase credentials in `.env`:**
   ```bash
   # document-api/.env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your-anon-key
   ```

### Step 1: Review Deployment Script

The `deploy-cloudrun.sh` script will:

1. ✅ Load Supabase credentials from `.env`
2. ✅ Build Docker image using Google Cloud Build
3. ✅ Push image to Google Container Registry
4. ✅ Deploy to Cloud Run with all environment variables (including auth)
5. ✅ Test the deployed API

### Step 2: Run Deployment Script

```bash
cd document-api

# Make script executable (if not already)
chmod +x deploy-cloudrun.sh

# Deploy to Cloud Run
./deploy-cloudrun.sh
```

**What happens:**

```
🚀 Deploying Document API to Google Cloud Run...
🔧 Setting Google Cloud project...
🔌 Enabling required APIs...
🏗️  Building Docker image...
🌐 Deploying to Cloud Run...
🎉 Deployment complete!
📍 Service URL: https://document-api-XXXXX.us-central1.run.app
```

The script takes 5-10 minutes to complete.

### Step 3: Verify Cloud Deployment

**Test health endpoint:**

```bash
# Replace with your actual Cloud Run URL
CLOUD_URL="https://document-api-169798107925.us-central1.run.app"

curl ${CLOUD_URL}/health
```

**Test authentication:**

```bash
export TOKEN="your-jwt-token"
export CLOUD_URL="https://document-api-169798107925.us-central1.run.app"

# Test creating collection
curl -X POST ${CLOUD_URL}/collections \
  -H "Authorization: Bearer $TOKEN" \
  -F "name=Cloud Test Collection"

# Test listing collections
curl -X GET ${CLOUD_URL}/collections \
  -H "Authorization: Bearer $TOKEN"
```

### Step 4: Update Frontend to Use Cloud API

**Option A: Switch frontend to cloud (for production):**

Edit `/agent-chat-ui/.env`:

```bash
# Document Upload API Configuration
# Cloud deployment: https://document-api-169798107925.us-central1.run.app
# Local Docker: http://localhost:8000
NEXT_PUBLIC_DOCUMENT_API_URL=https://document-api-169798107925.us-central1.run.app
```

**Option B: Keep using local for development:**

Leave it as `http://localhost:8000` and only change when deploying frontend.

### Step 5: Test from Frontend with Cloud API

1. Update frontend `.env` to cloud URL
2. Restart frontend: `pnpm dev`
3. Sign in to frontend
4. Test document upload/collection creation
5. Check browser DevTools > Network tab for API calls

### Viewing Cloud Logs

```bash
# View recent logs
gcloud run services logs read document-api \
  --region us-central1 \
  --limit 50

# Follow logs in real-time
gcloud run services logs tail document-api \
  --region us-central1

# View authentication-related logs
gcloud run services logs read document-api \
  --region us-central1 \
  --limit 100 | grep -i auth
```

### Updating Cloud Deployment

When you make code changes:

```bash
cd document-api

# Simply run the deploy script again
./deploy-cloudrun.sh
```

The script will:

1. Rebuild the Docker image with your latest code
2. Push to Container Registry
3. Update the Cloud Run service
4. Zero-downtime deployment (Cloud Run handles this automatically)

### Manual Deployment (Alternative)

If you prefer manual control:

```bash
# Build and push image
gcloud builds submit --tag gcr.io/metatask-461115/document-api

# Deploy to Cloud Run
gcloud run deploy document-api \
    --image gcr.io/metatask-461115/document-api \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars "GCP_PROJECT_ID=metatask-461115" \
    --set-env-vars "VERTEX_AI_DATA_STORE_ID=metatask_1761751621392" \
    --set-env-vars "VERTEX_AI_LOCATION=global" \
    --set-env-vars "GCS_BUCKET_NAME=metatask-documents-bucket" \
    --set-env-vars "POSTGRES_HOST=34.69.160.99" \
    --set-env-vars "POSTGRES_PORT=5432" \
    --set-env-vars "POSTGRES_USER=tafadzwabwakura" \
    --set-env-vars "POSTGRES_PASSWORD=" \
    --set-env-vars "POSTGRES_DB=vertex_ai_documents" \
    --set-env-vars "SUPABASE_URL=https://nbjnhzmkwrgmamfuwfae.supabase.co" \
    --set-env-vars "SUPABASE_ANON_KEY=your-key-here" \
    --memory 512Mi \
    --timeout 300 \
    --port 8080
```

### Troubleshooting Cloud Deployment

**Build fails:**

```bash
# Check build logs
gcloud builds list --limit 5

# View specific build
gcloud builds log [BUILD_ID]
```

**Deployment succeeds but API doesn't work:**

```bash
# Check Cloud Run logs
gcloud run services logs read document-api --region us-central1 --limit 100

# Check if environment variables are set
gcloud run services describe document-api --region us-central1 --format="value(spec.template.spec.containers[0].env)"
```

**Authentication errors in cloud:**

- Verify Supabase URL and key are correct in Cloud Run
- Check logs for "Authentication failed" messages
- Test JWT token is valid and not expired
- Ensure Cloud Run has correct SUPABASE_URL and SUPABASE_ANON_KEY

**Can't connect to database:**

- Verify POSTGRES_HOST IP is correct (34.69.160.99)
- Check Cloud SQL firewall rules allow Cloud Run
- Verify database credentials

---

## Quick Reference Commands

### Docker Commands

```bash
# Start
docker-compose up -d --build

# Stop
docker-compose down

# View logs
docker-compose logs -f api

# Restart
docker-compose restart api

# Rebuild and restart
docker-compose up -d --build --force-recreate
```

### Cloud Run Commands

```bash
# Deploy (using script)
./deploy-cloudrun.sh

# View logs
gcloud run services logs read document-api --region us-central1 --limit 50

# Get service URL
gcloud run services describe document-api --region us-central1 --format="value(status.url)"

# Delete service
gcloud run services delete document-api --region us-central1

# View all services
gcloud run services list
```

### Testing Commands

```bash
# Get JWT token (browser console)
const token = JSON.parse(localStorage.getItem('supabase.auth.token'))?.currentSession?.access_token;
copy(token);

# Test local Docker
curl -X GET http://localhost:8000/collections -H "Authorization: Bearer $TOKEN"

# Test Cloud Run
curl -X GET https://document-api-169798107925.us-central1.run.app/collections -H "Authorization: Bearer $TOKEN"
```

---

## Summary Checklist

### Local Docker Testing:

- [ ] Docker Desktop is running
- [ ] `.env.docker` file exists with Supabase credentials
- [ ] Run `./docker-start.sh` successfully
- [ ] Health endpoint responds: `curl http://localhost:8000/health`
- [ ] Authentication works: Test with JWT token via curl
- [ ] Frontend connects to local Docker API
- [ ] Can create collections and upload documents

### Cloud Deployment:

- [ ] Google Cloud SDK installed and authenticated
- [ ] `.env` file has Supabase credentials
- [ ] Run `./deploy-cloudrun.sh` successfully
- [ ] Cloud health endpoint responds
- [ ] Authentication works in cloud
- [ ] Update frontend `.env` with cloud URL (when ready)
- [ ] Test end-to-end from deployed frontend

---

## Need Help?

**Check logs:**

- Docker: `docker-compose logs -f api`
- Cloud Run: `gcloud run services logs read document-api --region us-central1`

**Review documentation:**

- Authentication: `AUTHENTICATION.md`
- Testing: `TESTING_DOCUMENT_API_AUTH.md`
- Deployment: `DEPLOYMENT.md`

**Common issues:**

- Port 8000 conflict: Stop other services or change port in docker-compose.yml
- PostgreSQL connection: Verify host.docker.internal works or use actual IP
- Authentication: Ensure Supabase credentials match between frontend and backend
- Cloud Build timeout: Increase timeout with `--timeout=20m` flag

---

**Happy deploying! 🚀**
