# Quick Start: Document Manager Integration

This is a **5-minute guide** to get the Document Manager up and running in the Agent Chat UI.

## Prerequisites

- Node.js 18+ and pnpm installed
- Python 3.8+ for the Document API backend
- Document API backend code in `document-api/` folder

## Step 1: Start the Document API Backend (2 minutes)

```bash
# Navigate to the document API folder
cd document-api

# Activate virtual environment (if it exists, otherwise create it)
source venv/bin/activate
# OR create it: python -m venv venv && source venv/bin/activate

# Install dependencies (if needed)
pip install -r requirements.txt

# Make sure .env is configured
# Edit document-api/.env with your GCP credentials

# Start the API server
python main.py
```

The API should start at: **http://localhost:8000**

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Step 2: Verify Backend is Running

Open another terminal and test:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "gcp_project": "your-project-id",
  "datastore_id": "your-datastore-id",
  "bucket": "your-bucket-name"
}
```

## Step 3: Start the Agent Chat UI (1 minute)

```bash
# Navigate back to the agent-chat-ui folder
cd /Users/tafadzwabwakura/agent-chat-ui

# Install dependencies (if not already done)
pnpm install

# Verify .env has the Document API URL
cat .env | grep DOCUMENT_API_URL
# Should show: NEXT_PUBLIC_DOCUMENT_API_URL=http://localhost:8000

# Start the development server
pnpm dev
```

The UI should start at: **http://localhost:3000**

## Step 4: Use the Document Manager (2 minutes)

1. **Open the UI**: Navigate to http://localhost:3000 in your browser

2. **Start a chat**: Type any message to start a thread (or load an existing thread)

3. **Open Document Manager**:
   - Look for the **document/file icon** in the top-right toolbar
   - Click it to open the Document Manager panel

4. **Create a Collection**:
   - Click **"New Collection"** button
   - Enter a name like "Test Collection"
   - Click **"Create"**

5. **Upload a Document**:
   - Make sure your collection is selected
   - Click the file input button
   - Select a PDF, DOCX, TXT, or HTML file
   - Click **"Upload Files"**
   - Watch the progress bar!

6. **View Your Documents**:
   - Documents will appear in the list
   - You can see filename, size, type, and upload date

## That's it! 🎉

You now have a fully functional document management system integrated into your Agent Chat UI!

## Quick Troubleshooting

**Q: Document Manager button doesn't appear**
- A: Make sure you've started a chat thread first (send a message)

**Q: "Failed to load collections" error**
- A: Check that the Document API is running on port 8000
- Run: `curl http://localhost:8000/health`

**Q: Upload button is disabled**
- A: Make sure you've selected a collection first
- Then select files to upload

**Q: Upload fails**
- A: Check the file type (must be PDF, DOCX, TXT, or HTML)
- Check file size (must be under 32MB)
- Check the backend logs for errors

## What Happens After Upload?

1. **Immediate**: File is uploaded to Google Cloud Storage
2. **5-30 minutes**: Vertex AI Search processes the document:
   - Extracts text
   - Chunks content
   - Generates embeddings
   - Indexes for search
3. **Complete**: Document is searchable in Vertex AI!

## Next Steps

- Read [DOCUMENT_MANAGER_INTEGRATION.md](./DOCUMENT_MANAGER_INTEGRATION.md) for detailed documentation
- Check the Document API docs in `document-api/README.md`
- Customize the user ID in the integration
- Deploy to production (see DEPLOYMENT.md)

## File Structure Overview

```
agent-chat-ui/
├── src/
│   ├── types/
│   │   └── document-api.ts          # TypeScript types
│   ├── lib/
│   │   └── document-api-client.ts   # API client
│   ├── hooks/
│   │   └── use-document-collections.tsx  # React hooks
│   ├── components/
│   │   ├── document-manager/
│   │   │   └── index.tsx            # Main UI component
│   │   └── thread/
│   │       └── index.tsx            # Modified to integrate Document Manager
│   └── ...
├── .env                             # Environment config (updated)
└── document-api/                    # Backend API
    ├── main.py
    ├── config.py
    └── ...
```

## Development Tips

- **Hot reload**: Both frontend and backend support hot reload
- **Multiple files**: You can upload multiple files at once
- **Progress tracking**: Watch the upload progress in real-time
- **Collections**: Organize documents into logical groups

Enjoy your new Document Manager! 📁✨
