# FastAPI Document Upload for Vertex AI Search

A production-ready FastAPI service that accepts document uploads, stores them in Google Cloud Storage, and automatically triggers Vertex AI Search to process, chunk, embed, and index them.

## 🎯 What This Does

**SIMPLE VERSION - Let Vertex AI do the work!**

1. User uploads file → Your API
2. Your API uploads file → Google Cloud Storage bucket
3. Your API tells Vertex AI → "Import from this GCS path"
4. Vertex AI automatically:
   - Extracts text from PDF/DOCX/HTML/TXT
   - Chunks the document optimally
   - Generates embeddings
   - Indexes for search
5. Done! ✅

## 🏗️ Architecture

```
┌─────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   Client    │─────▶│  FastAPI Server │─────▶│  Google Cloud   │
│  (Upload)   │      │   (This Repo)   │      │    Storage      │
└─────────────┘      └─────────────────┘      └─────────────────┘
                              │                         │
                              │                         │
                              ▼                         ▼
                     ┌─────────────────────────────────────┐
                     │     Vertex AI Search Engine         │
                     │  (Auto: Parse → Chunk → Embed →     │
                     │         Index)                      │
                     └─────────────────────────────────────┘
```

## ✨ Features

- ✅ **Multiple file upload** - Upload single or multiple documents at once
- ✅ **Automatic processing** - Vertex AI handles text extraction, chunking, and indexing
- ✅ **File type support** - PDF, DOCX, TXT, HTML
- ✅ **Unique filenames** - Prevents collisions with UUID prefixes
- ✅ **INCREMENTAL imports** - New documents don't affect existing ones
- ✅ **Comprehensive error handling** - Clear error messages and logging
- ✅ **Health checks** - Monitor service status
- ✅ **Operation tracking** - Check import status
- ✅ **Production-ready** - Proper configuration, logging, and validation

## 📋 Prerequisites

### 1. Google Cloud Project Setup

1. Create or select a [Google Cloud Project](https://console.cloud.google.com/projectcreate)
2. Enable billing on your project
3. Enable required APIs:
   ```bash
   gcloud services enable discoveryengine.googleapis.com
   gcloud services enable storage.googleapis.com
   ```

### 2. Vertex AI Search Datastore

**Create a datastore** (if you haven't already):

```bash
# Using gcloud (replace with your values)
gcloud alpha discovery-engine data-stores create YOUR_DATASTORE_ID \
  --location=global \
  --industry-vertical=GENERIC \
  --solution-type=SOLUTION_TYPE_SEARCH \
  --content-config=CONTENT_REQUIRED
```

Or create via [Cloud Console](https://console.cloud.google.com/gen-app-builder/data-stores).

**Get your datastore ID:**
- Go to [Vertex AI Search Console](https://console.cloud.google.com/gen-app-builder/data-stores)
- Click on your datastore
- Copy the datastore ID from the URL or details page

### 3. Google Cloud Storage Bucket

**Create a GCS bucket:**

```bash
# Option 1: Create bucket manually
gsutil mb -p YOUR_PROJECT_ID gs://YOUR_BUCKET_NAME

# Option 2: Let the API create it (requires appropriate permissions)
# Just specify the bucket name in .env and it will be created on startup
```

### 4. Authentication

**Option A: Using gcloud (for local development)**
```bash
gcloud auth application-default login
```

**Option B: Using Service Account (for production)**
```bash
# 1. Create service account
gcloud iam service-accounts create vertex-ai-upload \
  --display-name="Vertex AI Document Upload Service"

# 2. Grant required roles
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:vertex-ai-upload@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/discoveryengine.editor"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:vertex-ai-upload@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

# 3. Download key
gcloud iam service-accounts keys create key.json \
  --iam-account=vertex-ai-upload@YOUR_PROJECT_ID.iam.gserviceaccount.com

# 4. Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
```

## 🚀 Installation & Setup

### 1. Clone and Navigate

```bash
cd fastapi-document-upload
```

### 2. Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your values
nano .env  # or use your favorite editor
```

**Required configuration in `.env`:**

```env
GCP_PROJECT_ID=metatask-461115
VERTEX_AI_DATA_STORE_ID=metatask_1761751621392
VERTEX_AI_LOCATION=global
GCS_BUCKET_NAME=metatask-documents-bucket
```

### 4. Run the Server

```bash
# Development mode (with auto-reload)
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode (without reload)
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

Server will start at: `http://localhost:8000`

## 📚 API Documentation

Once the server is running, access:

- **Interactive API Docs (Swagger UI):** http://localhost:8000/docs
- **Alternative API Docs (ReDoc):** http://localhost:8000/redoc

## 🔌 API Endpoints

### 1. Health Check

**GET** `/health`

Check if the service is running and properly configured.

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "gcp_project": "metatask-461115",
  "datastore_id": "metatask_1761751621392",
  "bucket": "metatask-documents-bucket"
}
```

---

### 2. Upload Documents

**POST** `/upload`

Upload one or more documents for indexing in Vertex AI Search.

**Request:**
```bash
# Single file
curl -X POST "http://localhost:8000/upload" \
  -H "accept: application/json" \
  -F "files=@document.pdf"

# Multiple files
curl -X POST "http://localhost:8000/upload" \
  -H "accept: application/json" \
  -F "files=@document1.pdf" \
  -F "files=@document2.docx" \
  -F "files=@document3.txt"
```

**Success Response (202 Accepted):**
```json
{
  "status": "accepted",
  "message": "Successfully uploaded 2 document(s) to GCS and triggered indexing",
  "documents": [
    {
      "original_filename": "document1.pdf",
      "document_id": "a1b2c3d4e5f6_document1.pdf",
      "gcs_uri": "gs://metatask-documents-bucket/a1b2c3d4e5f6_document1.pdf",
      "size_bytes": 245678,
      "content_type": "application/pdf"
    },
    {
      "original_filename": "document2.docx",
      "document_id": "g7h8i9j0k1l2_document2.docx",
      "gcs_uri": "gs://metatask-documents-bucket/g7h8i9j0k1l2_document2.docx",
      "size_bytes": 156789,
      "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    }
  ],
  "vertex_ai_import": {
    "triggered": true,
    "operation_name": "projects/123456/locations/global/collections/default_collection/dataStores/metatask_1761751621392/branches/default_branch/operations/import-documents-789012",
    "status_message": "Vertex AI Search is now processing, chunking, embedding, and indexing your documents"
  }
}
```

**Error Response (400 Bad Request):**
```json
{
  "detail": {
    "message": "No files were successfully uploaded",
    "failed_uploads": [
      {
        "filename": "invalid.exe",
        "error": "Invalid file type: .exe. Allowed types: .pdf, .docx, .txt, .html, .htm"
      }
    ]
  }
}
```

---

### 3. Check Operation Status

**GET** `/operation/{operation_name}`

Check the status of a document import operation.

```bash
curl "http://localhost:8000/operation/projects/123456/locations/global/collections/default_collection/dataStores/metatask_1761751621392/branches/default_branch/operations/import-documents-789012"
```

**Response:**
```json
{
  "done": true,
  "name": "projects/123456/.../operations/import-documents-789012",
  "success": true,
  "create_time": "2024-01-15T10:30:00Z",
  "update_time": "2024-01-15T10:32:45Z"
}
```

## 🧪 Testing with Python

```python
import requests

# Upload single document
with open("document.pdf", "rb") as f:
    files = {"files": ("document.pdf", f, "application/pdf")}
    response = requests.post("http://localhost:8000/upload", files=files)
    print(response.json())

# Upload multiple documents
files = [
    ("files", ("doc1.pdf", open("doc1.pdf", "rb"), "application/pdf")),
    ("files", ("doc2.docx", open("doc2.docx", "rb"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
]
response = requests.post("http://localhost:8000/upload", files=files)
print(response.json())
```

## 📁 Project Structure

```
fastapi-document-upload/
├── main.py                  # FastAPI application with endpoints
├── config.py                # Configuration management (env vars)
├── gcs_uploader.py          # Google Cloud Storage upload logic
├── vertex_ai_importer.py    # Vertex AI Search import logic
├── requirements.txt         # Python dependencies
├── .env.example             # Example environment configuration
├── .env                     # Your actual configuration (gitignored)
└── README.md                # This file
```

## 🔧 Configuration Options

All configuration is done via environment variables in `.env`:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GCP_PROJECT_ID` | ✅ Yes | - | Your Google Cloud project ID |
| `VERTEX_AI_DATA_STORE_ID` | ✅ Yes | - | Your Vertex AI Search datastore ID |
| `VERTEX_AI_LOCATION` | No | `global` | Datastore location (global/us/eu) |
| `GCS_BUCKET_NAME` | ✅ Yes | - | GCS bucket for document storage |
| `MAX_FILE_SIZE` | No | `33554432` | Max file size in bytes (32MB) |
| `ALLOWED_EXTENSIONS` | No | `[".pdf", ".docx", ".txt", ".html", ".htm"]` | Allowed file extensions |
| `API_TITLE` | No | Auto | API title for docs |
| `API_VERSION` | No | `1.0.0` | API version |

## 🐛 Troubleshooting

### Issue: "Permission denied" errors

**Solution:** Ensure your service account or user has these roles:
- `roles/discoveryengine.editor` - For Vertex AI Search
- `roles/storage.objectAdmin` - For Cloud Storage

```bash
# Check current permissions
gcloud projects get-iam-policy YOUR_PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:YOUR_EMAIL"
```

### Issue: "Bucket does not exist"

**Solution:** Create the bucket manually:
```bash
gsutil mb -p YOUR_PROJECT_ID gs://YOUR_BUCKET_NAME
```

### Issue: "Datastore not found"

**Solution:** Verify your datastore ID:
```bash
gcloud alpha discovery-engine data-stores list --location=global
```

### Issue: Import triggered but documents not appearing

**Cause:** Document processing takes time (a few minutes to hours depending on size).

**Solution:**
1. Check operation status via API: `/operation/{operation_name}`
2. View activity in [Cloud Console](https://console.cloud.google.com/gen-app-builder/data-stores)
3. Large PDFs may take 10-30 minutes to process

### Issue: "Invalid file type" errors

**Solution:** Only these types are supported:
- PDF: `.pdf`
- Word: `.docx` (not `.doc`)
- Text: `.txt`
- HTML: `.html`, `.htm`

### Issue: Module import errors

**Solution:**
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade

# If using virtual environment, make sure it's activated
source venv/bin/activate
```

## 📊 Monitoring

### View Logs

```bash
# Application logs appear in stdout/stderr
# For production, redirect to file:
uvicorn main:app --host 0.0.0.0 --port 8000 > app.log 2>&1
```

### Check Import Activity

1. Go to [Vertex AI Search Console](https://console.cloud.google.com/gen-app-builder/data-stores)
2. Click your datastore
3. Navigate to **Activity** tab
4. View import operations and status

### Monitor GCS Bucket

```bash
# List uploaded files
gsutil ls gs://YOUR_BUCKET_NAME/

# View file details
gsutil ls -l gs://YOUR_BUCKET_NAME/
```

## 🚀 Deployment

### Deploy to Cloud Run

```bash
# 1. Build container
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/vertex-ai-upload

# 2. Deploy to Cloud Run
gcloud run deploy vertex-ai-upload \
  --image gcr.io/YOUR_PROJECT_ID/vertex-ai-upload \
  --platform managed \
  --region us-central1 \
  --set-env-vars GCP_PROJECT_ID=YOUR_PROJECT_ID \
  --set-env-vars VERTEX_AI_DATA_STORE_ID=YOUR_DATASTORE_ID \
  --set-env-vars GCS_BUCKET_NAME=YOUR_BUCKET_NAME \
  --allow-unauthenticated
```

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Deploy to Google Compute Engine / VM

```bash
# 1. SSH into your VM
gcloud compute ssh YOUR_VM_NAME

# 2. Clone repo and setup
git clone YOUR_REPO
cd fastapi-document-upload
pip install -r requirements.txt

# 3. Create systemd service
sudo nano /etc/systemd/system/vertex-ai-upload.service
```

Service file content:
```ini
[Unit]
Description=Vertex AI Document Upload API
After=network.target

[Service]
User=YOUR_USER
WorkingDirectory=/path/to/fastapi-document-upload
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable vertex-ai-upload
sudo systemctl start vertex-ai-upload
```

## 📖 Additional Resources

- [Vertex AI Search Documentation](https://cloud.google.com/generative-ai-app-builder/docs/introduction)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Google Cloud Storage Python Client](https://cloud.google.com/python/docs/reference/storage/latest)
- [Vertex AI Search Python Client](https://cloud.google.com/python/docs/reference/discoveryengine/latest)

## 🤝 Support

For issues or questions:
1. Check the [Troubleshooting](#-troubleshooting) section
2. Review [Vertex AI Search documentation](https://cloud.google.com/generative-ai-app-builder/docs)
3. Check application logs for detailed error messages

## 📝 License

Copyright 2024 - Based on Google Cloud Vertex AI Search examples

## 🙏 Acknowledgments

This implementation is based on patterns from the [Google Cloud Generative AI repository](https://github.com/GoogleCloudPlatform/generative-ai), specifically:
- `create_datastore_and_search.ipynb` - Document import patterns
- `vais-building-blocks/ingesting_unstructured_documents_with_metadata.ipynb` - GCS upload workflow
- `cloud-function/python/` - API structure and error handling
