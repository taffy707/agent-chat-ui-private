# Document Manager Integration Guide

This guide explains how the Document Upload API has been integrated into the Agent Chat UI.

## Overview

The Agent Chat UI now includes a **Document Manager** that allows users to:
- Create and manage document collections
- Upload documents (PDF, DOCX, TXT, HTML) to collections
- View all uploaded documents
- Delete documents and collections
- Track upload progress in real-time

The documents are uploaded to a FastAPI backend service that stores them in Google Cloud Storage and automatically indexes them in Vertex AI Search.

## Architecture

```
┌─────────────────────┐      ┌──────────────────────┐      ┌─────────────────┐
│  Agent Chat UI      │─────▶│  Document Upload API │─────▶│  Google Cloud   │
│  (Next.js)          │      │  (FastAPI)           │      │  Storage        │
│  - Document Manager │      │  - Collections       │      └─────────────────┘
│  - Upload UI        │      │  - Upload Handler    │               │
└─────────────────────┘      └──────────────────────┘               │
                                      │                              │
                                      │                              ▼
                                      │                     ┌─────────────────┐
                                      └────────────────────▶│  Vertex AI      │
                                                            │  Search Engine  │
                                                            └─────────────────┘
```

## Files Added

### TypeScript Types
- **`src/types/document-api.ts`**: TypeScript interfaces for API requests/responses
  - `Collection`, `Document`, `UploadResponse`, etc.

### API Client
- **`src/lib/document-api-client.ts`**: API client for communicating with the Document Upload API
  - Handles all HTTP requests to the backend
  - Supports upload progress tracking
  - Includes error handling

### React Hooks
- **`src/hooks/use-document-collections.tsx`**: Custom hooks for document management
  - `useDocumentCollections()`: Manage collections (create, list, delete)
  - `useDocuments()`: Manage documents (upload, list, delete)

### UI Components
- **`src/components/document-manager/index.tsx`**: Main Document Manager component
  - Collections sidebar
  - Document list view
  - Upload interface with progress tracking
  - Delete functionality

### Integration
- **Modified `src/components/thread/index.tsx`**:
  - Added Document Manager button to toolbar
  - Integrated Sheet component to display Document Manager
  - Added state management for opening/closing the manager

### Configuration
- **Updated `.env`** and **`.env.example`**:
  - Added `NEXT_PUBLIC_DOCUMENT_API_URL` environment variable

## Setup Instructions

### 1. Backend API Setup

The Document Upload API should already be running. If not:

```bash
cd document-api
source venv/bin/activate
python main.py
```

The API will start at `http://localhost:8000`

### 2. Frontend Configuration

Ensure the `.env` file has the Document API URL configured:

```env
NEXT_PUBLIC_DOCUMENT_API_URL=http://localhost:8000
```

### 3. Install Dependencies (if needed)

All required dependencies are already in `package.json`:
- `@radix-ui/react-sheet` - For the sidebar UI
- `lucide-react` - For icons

### 4. Start the Frontend

```bash
pnpm install
pnpm dev
```

The frontend will start at `http://localhost:3000`

## Usage

### Accessing the Document Manager

1. Start a chat or open an existing thread
2. Click the **Document icon** (file/document icon) in the top toolbar
3. The Document Manager will slide in from the right

### Creating a Collection

1. Click **"New Collection"** button in the sidebar
2. Enter a collection name
3. Click **"Create"**

### Uploading Documents

1. Select a collection from the sidebar
2. Click the file input in the upload section
3. Select one or more files (PDF, DOCX, TXT, HTML)
4. Click **"Upload Files"**
5. Monitor the upload progress bar

### Viewing Documents

1. Select a collection from the sidebar
2. All documents in that collection will be displayed
3. Each document shows:
   - Filename
   - File size
   - File type
   - Upload date and time
   - Status

### Deleting Documents

1. Click the **trash icon** next to any document
2. Confirm the deletion
3. The document will be removed from the collection

### Deleting Collections

1. Hover over a collection in the sidebar
2. Click the **trash icon** that appears
3. Confirm the deletion (this will delete ALL documents in the collection)

## Features

### Upload Progress Tracking
- Real-time progress bar during file uploads
- Shows percentage completion
- Handles multiple file uploads

### Error Handling
- Toast notifications for success/error messages
- Clear error messages from the API
- Graceful fallback for failed requests

### Responsive Design
- Mobile-friendly interface
- Slide-out panel that doesn't interfere with chat
- Scrollable collections and documents lists

### User Management
Currently uses a default user ID (`"default-user"`). In production, you should:
1. Implement authentication
2. Get the actual user ID from your auth system
3. Pass it to the DocumentManager component

## API Endpoints Used

The integration uses these backend endpoints:

### Collections
- `POST /collections` - Create a new collection
- `GET /collections?user_id={id}` - List all collections
- `GET /collections/{id}` - Get collection details
- `DELETE /collections/{id}` - Delete a collection

### Documents
- `POST /upload` - Upload files to a collection
- `GET /collections/{id}/documents` - List documents in a collection
- `GET /documents?user_id={id}` - List all documents
- `DELETE /documents/{id}` - Delete a document

### Health
- `GET /health` - Check API status

## Environment Variables

### Frontend (.env)
```env
# Document Upload API URL
NEXT_PUBLIC_DOCUMENT_API_URL=http://localhost:8000
```

### Backend (document-api/.env)
```env
# Google Cloud Project Configuration
GCP_PROJECT_ID=your-project-id
VERTEX_AI_DATA_STORE_ID=your-datastore-id
VERTEX_AI_LOCATION=global
GCS_BUCKET_NAME=your-bucket-name

# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
POSTGRES_DB=vertex_ai_documents
```

## Customization

### Change User ID
Edit `src/components/thread/index.tsx`:

```typescript
<DocumentManager
  userId="your-actual-user-id" // Change this
  onClose={() => setDocumentManagerOpen(false)}
/>
```

### Change API URL
Edit `.env`:

```env
NEXT_PUBLIC_DOCUMENT_API_URL=https://your-api-domain.com
```

### Modify Accepted File Types
The file input accepts: `.pdf,.docx,.txt,.html,.htm`

To change this, edit `src/components/document-manager/index.tsx`:

```typescript
<Input
  type="file"
  multiple
  accept=".pdf,.docx,.txt,.html,.htm,.your-type" // Add more types
  onChange={handleFileSelect}
/>
```

### Customize UI Colors/Styles
The component uses Tailwind CSS classes. Modify styling in:
- `src/components/document-manager/index.tsx`

## Troubleshooting

### Document Manager button doesn't appear
- Ensure you're in a thread (not the welcome screen)
- Check browser console for errors

### "Failed to load collections" error
- Verify the Document API is running on port 8000
- Check `.env` has correct `NEXT_PUBLIC_DOCUMENT_API_URL`
- Verify CORS is configured in the backend (`main.py`)

### Upload fails
- Check file type is supported (PDF, DOCX, TXT, HTML)
- Verify file size is under 32MB (backend default limit)
- Check backend logs for detailed error messages

### Documents not appearing in Vertex AI Search
- Processing takes 5-30 minutes depending on file size
- Check Vertex AI Search console for import status
- Verify backend configuration (GCS bucket, datastore ID)

## Production Deployment

### Frontend
1. Update `.env.production`:
```env
NEXT_PUBLIC_DOCUMENT_API_URL=https://api.yourdomain.com
```

2. Build and deploy:
```bash
pnpm build
pnpm start
```

### Backend
See `document-api/DEPLOYMENT.md` for full deployment instructions to:
- Google Cloud Run
- Google Compute Engine
- Docker containers

## Next Steps

Potential enhancements:
- [ ] Add search functionality across documents
- [ ] Implement document preview
- [ ] Add metadata editing
- [ ] Support for more file types
- [ ] Batch upload with drag-and-drop
- [ ] Document sharing between users
- [ ] Integration with chat for document-based Q&A

## Support

For issues or questions:
1. Check the Document API documentation in `document-api/README.md`
2. Review backend logs for API errors
3. Check browser console for frontend errors
4. Verify all environment variables are set correctly
