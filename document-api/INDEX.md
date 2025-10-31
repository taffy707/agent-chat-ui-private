# 📚 Documentation Index

Welcome! This is your guide to all documentation for the FastAPI Document Upload Service.

## 🚀 Quick Links

| What do you want to do? | Go here |
|-------------------------|---------|
| **Get started in 5 minutes** | [QUICKSTART.md](QUICKSTART.md) |
| **Understand the architecture** | [ARCHITECTURE.md](ARCHITECTURE.md) |
| **Read full documentation** | [README.md](README.md) |
| **See what was built** | [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) |
| **Start coding** | [main.py](main.py) |

---

## 📖 Documentation Files

### 1. [QUICKSTART.md](QUICKSTART.md) ⚡
**5-minute setup guide**
- Ultra-fast setup if you already have GCP configured
- Step-by-step from scratch
- Quick testing commands
- Common issues & fixes
- Next steps

**Read this if:** You want to get running FAST

---

### 2. [README.md](README.md) 📘
**Complete documentation (15,000+ words)**
- What this does & why
- Architecture diagram
- Features list
- Prerequisites (detailed)
- Installation & setup
- API documentation
- Configuration options
- Testing guide
- Troubleshooting
- Deployment guide
- Additional resources

**Read this if:** You want comprehensive documentation

---

### 3. [ARCHITECTURE.md](ARCHITECTURE.md) 🏗️
**System architecture & design**
- System architecture diagram
- Request flow
- Component interactions
- Data flow diagrams
- Error handling flow
- Authentication flow
- Deployment architectures
- Performance characteristics
- Scalability considerations

**Read this if:** You want to understand HOW it works

---

### 4. [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) 📦
**What was built & why**
- Features delivered
- Project structure
- How it works
- Core components
- API endpoints
- Configuration
- Dependencies
- Testing
- What you learned
- Comparison with repo
- Success criteria

**Read this if:** You want to understand WHAT was built

---

### 5. [.env.example](.env.example) ⚙️
**Configuration template**
- All required environment variables
- Your specific values (metatask-*)
- Optional settings
- Comments explaining each setting

**Read this if:** You need to configure the app

---

## 💻 Code Files

### Core Application Files

#### [main.py](main.py)
**FastAPI application (450+ lines)**
- `/upload` endpoint - Upload documents
- `/health` endpoint - Health checks
- `/operation/{name}` endpoint - Check import status
- Request validation
- Error handling
- Logging

**Key functions:**
- `upload_documents()` - Main upload handler
- `validate_file()` - File validation
- `check_operation_status()` - Import status

---

#### [config.py](config.py)
**Configuration management (50 lines)**
- Environment variable loading
- Settings validation
- Type hints with Pydantic
- Default values

**Key class:**
- `Settings(BaseSettings)` - Application config

---

#### [gcs_uploader.py](gcs_uploader.py)
**Google Cloud Storage operations (100+ lines)**
- Upload files to GCS
- Generate unique filenames with UUIDs
- Delete files
- Bucket management

**Key class & methods:**
- `GCSUploader` class
  - `upload_file()` - Upload with unique name
  - `generate_unique_filename()` - UUID prefixes
  - `delete_file()` - Remove files
  - `ensure_bucket_exists()` - Bucket checks

---

#### [vertex_ai_importer.py](vertex_ai_importer.py)
**Vertex AI Search integration (150+ lines)**
- Trigger document imports
- INCREMENTAL reconciliation mode
- Operation status checking
- Long-running operation handling

**Key class & methods:**
- `VertexAIImporter` class
  - `import_documents_from_gcs()` - Trigger import
  - `check_operation_status()` - Poll status

---

### Supporting Files

#### [test_upload.py](test_upload.py)
**Testing utility (100 lines)**
- Command-line test script
- Health check validation
- Upload testing
- Response parsing

**Usage:**
```bash
python test_upload.py document.pdf
```

---

#### [setup.sh](setup.sh)
**Automated setup script (80 lines)**
- Check Python installation
- Create virtual environment
- Install dependencies
- Configure .env
- Check authentication

**Usage:**
```bash
./setup.sh
```

---

#### [Dockerfile](Dockerfile)
**Container definition**
- Python 3.11 slim base
- Dependencies installation
- Health check
- Port 8080 exposure
- Production command

**Usage:**
```bash
docker build -t vertex-ai-upload .
docker run -p 8080:8080 --env-file .env vertex-ai-upload
```

---

#### [requirements.txt](requirements.txt)
**Python dependencies**
- FastAPI & uvicorn
- Google Cloud libraries
- Pydantic for config
- Development tools

**Install:**
```bash
pip install -r requirements.txt
```

---

#### [.gitignore](.gitignore)
**Git ignore rules**
- Environment files (.env)
- Service account keys (*.json)
- Python artifacts
- IDE files
- OS files

---

## 🎯 Usage Scenarios

### Scenario 1: "I just want to see if this works"
1. Read: [QUICKSTART.md](QUICKSTART.md)
2. Run: `./setup.sh`
3. Edit: `.env`
4. Run: `python main.py`
5. Test: `python test_upload.py test.txt`

---

### Scenario 2: "I need to understand the code"
1. Read: [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
2. Read: [ARCHITECTURE.md](ARCHITECTURE.md)
3. Review: [main.py](main.py)
4. Review: [gcs_uploader.py](gcs_uploader.py)
5. Review: [vertex_ai_importer.py](vertex_ai_importer.py)

---

### Scenario 3: "I need to deploy to production"
1. Read: [README.md](README.md) → Deployment section
2. Review: [Dockerfile](Dockerfile)
3. Configure: Production environment variables
4. Deploy: Cloud Run / Compute Engine
5. Test: Production endpoints

---

### Scenario 4: "I want to add features"
1. Read: [ARCHITECTURE.md](ARCHITECTURE.md)
2. Review: Existing code structure
3. Add: New module or extend existing
4. Test: With [test_upload.py](test_upload.py)
5. Document: Update [README.md](README.md)

---

### Scenario 5: "Something is broken"
1. Check: [README.md](README.md) → Troubleshooting
2. Check: [QUICKSTART.md](QUICKSTART.md) → Common Issues
3. Check: Application logs
4. Check: GCP Console activity
5. Ask: With detailed error messages

---

## 🔍 Code Reference

### Finding Specific Functionality

**Upload Handling:**
- Endpoint: [main.py](main.py) → `upload_documents()`
- Validation: [main.py](main.py) → `validate_file()`
- GCS upload: [gcs_uploader.py](gcs_uploader.py) → `upload_file()`

**Configuration:**
- Loading: [config.py](config.py) → `Settings` class
- Environment: [.env.example](.env.example)

**Vertex AI Integration:**
- Import trigger: [vertex_ai_importer.py](vertex_ai_importer.py) → `import_documents_from_gcs()`
- Status check: [vertex_ai_importer.py](vertex_ai_importer.py) → `check_operation_status()`

**Error Handling:**
- Validation errors: [main.py](main.py) → `validate_file()`
- Upload errors: [main.py](main.py) → `upload_documents()` try/except blocks
- Response errors: [main.py](main.py) → HTTPException raises

**Testing:**
- Test script: [test_upload.py](test_upload.py)
- Health check: [main.py](main.py) → `health_check()`

---

## 📊 File Statistics

```
Total Files: 14
Total Lines of Code: ~1,500
Total Documentation: ~25,000 words

Breakdown:
• Python code: 750 lines (main.py, config.py, etc.)
• Documentation: 20,000+ words (README, guides)
• Configuration: 50 lines (.env.example, Dockerfile)
• Scripts: 200 lines (setup.sh, test_upload.py)
```

---

## 🗺️ Learning Path

### Beginner
1. ✅ Read [QUICKSTART.md](QUICKSTART.md)
2. ✅ Run `./setup.sh`
3. ✅ Start server and test upload
4. ✅ Browse interactive docs at `/docs`
5. ✅ Read [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)

### Intermediate
1. ✅ Read [README.md](README.md) fully
2. ✅ Review [main.py](main.py) code
3. ✅ Understand [ARCHITECTURE.md](ARCHITECTURE.md)
4. ✅ Modify configuration settings
5. ✅ Add custom validation logic

### Advanced
1. ✅ Study all code files
2. ✅ Add new features (metadata, webhooks)
3. ✅ Deploy to Cloud Run
4. ✅ Set up monitoring & alerting
5. ✅ Implement rate limiting

---

## 🎓 Key Concepts

### FastAPI Concepts
- **Async endpoints** - Non-blocking I/O
- **File uploads** - UploadFile handling
- **Response models** - Pydantic validation
- **Error handling** - HTTPException
- **Auto documentation** - Swagger/ReDoc

**Learn in:** [main.py](main.py)

### Google Cloud Concepts
- **Cloud Storage** - Object storage
- **Vertex AI Search** - Document indexing
- **Service accounts** - Authentication
- **Long-running operations** - Async processing

**Learn in:** [gcs_uploader.py](gcs_uploader.py), [vertex_ai_importer.py](vertex_ai_importer.py)

### Design Patterns
- **Configuration pattern** - Settings class
- **Service layer** - Business logic separation
- **Error accumulation** - Continue on partial failures
- **UUID generation** - Unique identifiers

**Learn in:** [config.py](config.py), all modules

---

## 🔧 Customization Guide

### Add New File Type

**Where:** [config.py](config.py)
```python
ALLOWED_EXTENSIONS = [".pdf", ".docx", ".txt", ".html", ".new"]
ALLOWED_MIME_TYPES = ["...", "application/new-type"]
```

### Change Upload Size Limit

**Where:** [.env](.env)
```env
MAX_FILE_SIZE=67108864  # 64MB
```

### Add Metadata Support

**Where:** [main.py](main.py)
- Add metadata field to upload endpoint
- Pass to `gcs_uploader.upload_file()`
- Create JSONL format like in repository examples

### Add Authentication

**Where:** [main.py](main.py)
```python
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/upload", dependencies=[Depends(security)])
async def upload_documents(...):
    ...
```

### Add Webhook Notifications

**Where:** New file `webhooks.py` + [main.py](main.py)
- Create webhook sender
- Call after successful upload
- Include document IDs and status

---

## 💡 Tips & Tricks

### Development
- Use `--reload` flag for hot reloading
- Check logs for detailed error info
- Use `/docs` for interactive testing
- Test with small files first

### Production
- Use service account authentication
- Set up Cloud Monitoring
- Enable Cloud Logging
- Use Cloud Run for scaling
- Set memory/CPU limits

### Debugging
- Check health endpoint first
- Verify .env configuration
- Test GCS access separately
- Check datastore exists
- Review import operation status

---

## 📞 Getting Help

### Order of Operations
1. Check: [QUICKSTART.md](QUICKSTART.md) → Common Issues
2. Check: [README.md](README.md) → Troubleshooting
3. Review: Application logs
4. Check: GCP Console → Activity tab
5. Search: Error messages in docs

### Useful Commands
```bash
# Check health
curl http://localhost:8000/health

# View logs
# (logs appear in stdout/stderr)

# Test authentication
gcloud auth application-default print-access-token

# Check datastore
gcloud alpha discovery-engine data-stores list --location=global

# List bucket contents
gsutil ls gs://YOUR_BUCKET_NAME/
```

---

## ✅ Checklist Before Running

- [ ] Python 3.8+ installed
- [ ] Google Cloud project created
- [ ] Vertex AI Search datastore created
- [ ] GCS bucket created (or will be auto-created)
- [ ] APIs enabled (discoveryengine, storage)
- [ ] Authentication configured (gcloud or service account)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file configured with your values
- [ ] Virtual environment activated

**All set?** Run `python main.py` 🚀

---

## 📈 Next Steps After Setup

1. **Test locally** - Upload a few documents
2. **Monitor processing** - Check GCP Console activity
3. **Test search** - Query your documents
4. **Deploy** - Move to Cloud Run
5. **Enhance** - Add features you need
6. **Scale** - Configure autoscaling
7. **Monitor** - Set up alerts

---

**Built for:** `metatask-461115` project with datastore `metatask_1761751621392`

**Ready to start?** → [QUICKSTART.md](QUICKSTART.md) ⚡
