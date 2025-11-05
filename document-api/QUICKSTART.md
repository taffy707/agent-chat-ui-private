# 🚀 Quick Start Guide

Get your FastAPI Document Upload service running in 5 minutes!

## ⚡ Ultra-Fast Setup (Already Have Everything)

If you already have your GCP project, datastore, and bucket ready:

```bash
# 1. Run setup script
./setup.sh

# 2. Edit .env with your values
nano .env

# 3. Start the server
source venv/bin/activate
python main.py
```

**Done!** Visit http://localhost:8000/docs

---

## 📋 Step-by-Step Setup (From Scratch)

### Step 1: Google Cloud Prerequisites

```bash
# Login to Google Cloud
gcloud auth login
gcloud config set project metatask-461115

# Enable APIs
gcloud services enable discoveryengine.googleapis.com storage.googleapis.com

# Authenticate for local development
gcloud auth application-default login
```

### Step 2: Create Vertex AI Search Datastore

**Option A: Via Console (Easier)**

1. Go to https://console.cloud.google.com/gen-app-builder/data-stores
2. Click "Create Data Store"
3. Select "Unstructured documents"
4. Name: `metatask_datastore`
5. Location: `global`
6. Click "Create"
7. Copy the datastore ID from the URL

**Option B: Via gcloud**

```bash
gcloud alpha discovery-engine data-stores create metatask-datastore \
  --location=global \
  --industry-vertical=GENERIC \
  --solution-type=SOLUTION_TYPE_SEARCH \
  --content-config=CONTENT_REQUIRED
```

### Step 3: Create GCS Bucket

```bash
# Create bucket (replace with unique name)
gsutil mb -p metatask-461115 gs://metatask-documents-bucket

# Or let the API create it automatically
```

### Step 4: Install & Configure

```bash
# Run setup script
./setup.sh

# Edit .env file
nano .env
```

**Edit these values in `.env`:**

```env
GCP_PROJECT_ID=metatask-461115
VERTEX_AI_DATA_STORE_ID=metatask_1761751621392  # Your actual datastore ID
VERTEX_AI_LOCATION=global
GCS_BUCKET_NAME=metatask-documents-bucket  # Your bucket name
```

### Step 5: Start the Server

```bash
# Activate virtual environment
source venv/bin/activate

# Start server
python main.py
```

**Server is running!** 🎉

---

## 🧪 Test Your Setup

### Test 1: Health Check

```bash
curl http://localhost:8000/health
```

**Expected output:**

```json
{
  "status": "healthy",
  "gcp_project": "metatask-461115",
  "datastore_id": "metatask_1761751621392",
  "bucket": "metatask-documents-bucket"
}
```

### Test 2: Upload a Document

**Create a test file:**

```bash
echo "This is a test document for Vertex AI Search indexing." > test.txt
```

**Upload it:**

```bash
curl -X POST "http://localhost:8000/upload" \
  -F "files=@test.txt"
```

**Or use the test script:**

```bash
python test_upload.py test.txt
```

**Expected output:**

```json
{
  "status": "accepted",
  "message": "Successfully uploaded 1 document(s) to GCS and triggered indexing",
  "documents": [
    {
      "original_filename": "test.txt",
      "document_id": "abc123def456_test.txt",
      "gcs_uri": "gs://metatask-documents-bucket/abc123def456_test.txt",
      "size_bytes": 57,
      "content_type": "text/plain"
    }
  ],
  "vertex_ai_import": {
    "triggered": true,
    "operation_name": "projects/.../operations/import-documents-...",
    "status_message": "Vertex AI Search is now processing, chunking, embedding, and indexing your documents"
  }
}
```

### Test 3: Interactive API Docs

Open your browser: http://localhost:8000/docs

You can upload files directly from the Swagger UI!

---

## 📱 Upload from Different Clients

### Python

```python
import requests

with open("document.pdf", "rb") as f:
    files = {"files": ("document.pdf", f, "application/pdf")}
    response = requests.post("http://localhost:8000/upload", files=files)
    print(response.json())
```

### JavaScript/Node.js

```javascript
const FormData = require("form-data");
const fs = require("fs");

const form = new FormData();
form.append("files", fs.createReadStream("document.pdf"));

fetch("http://localhost:8000/upload", {
  method: "POST",
  body: form,
})
  .then((res) => res.json())
  .then((data) => console.log(data));
```

### cURL (Multiple Files)

```bash
curl -X POST "http://localhost:8000/upload" \
  -F "files=@document1.pdf" \
  -F "files=@document2.docx" \
  -F "files=@document3.txt"
```

### Postman

1. Method: `POST`
2. URL: `http://localhost:8000/upload`
3. Body → form-data
4. Key: `files` (set to File type)
5. Value: Select your file(s)
6. Send!

---

## ⏱️ How Long Does Processing Take?

After successful upload, Vertex AI Search processes documents in the background:

- **Small text files (< 100KB):** 1-5 minutes
- **PDFs (1-10 pages):** 5-15 minutes
- **Large PDFs (100+ pages):** 30-60 minutes
- **DOCX files:** 5-20 minutes

**Check progress:**

1. Console: https://console.cloud.google.com/gen-app-builder/data-stores
2. Click your datastore → "Activity" tab
3. Or use the API: `/operation/{operation_name}`

---

## 🔍 Verify Documents Are Indexed

### Option 1: Console

1. Go to https://console.cloud.google.com/gen-app-builder/data-stores
2. Click your datastore
3. Go to "Data" tab
4. You should see your uploaded documents

### Option 2: Search (After Processing)

The documents from this repo show how to query, or use the console:

1. Go to your datastore
2. Click "Preview" tab
3. Try searching for content from your document

---

## ❓ Common Issues & Quick Fixes

### Issue: "Permission denied"

**Fix:**

```bash
# Re-authenticate
gcloud auth application-default login
```

### Issue: "Bucket not found"

**Fix:**

```bash
# Create bucket
gsutil mb gs://YOUR_BUCKET_NAME
```

### Issue: "Datastore not found"

**Fix:**
Check your datastore ID:

```bash
gcloud alpha discovery-engine data-stores list --location=global
```

### Issue: "Module not found" errors

**Fix:**

```bash
# Activate venv and reinstall
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

### Issue: Port 8000 already in use

**Fix:**

```bash
# Use different port
uvicorn main:app --host 0.0.0.0 --port 8001
```

---

## 🎯 Next Steps

Once everything is working:

1. **Deploy to Production**

   - See README.md → Deployment section
   - Use Cloud Run for serverless deployment

2. **Add Authentication**

   - Integrate with Firebase Auth
   - Use API keys or OAuth

3. **Add Features**

   - Document metadata support
   - Webhook notifications on completion
   - Batch upload UI

4. **Monitor & Scale**
   - Add Cloud Monitoring
   - Configure autoscaling
   - Set up alerts

---

## 📚 More Resources

- Full documentation: [README.md](README.md)
- API reference: http://localhost:8000/docs (when running)
- Vertex AI Search docs: https://cloud.google.com/generative-ai-app-builder/docs
- Troubleshooting: See README.md → Troubleshooting section

---

**Got it working?** 🎉 You're now ready to index and search documents with Vertex AI Search!
