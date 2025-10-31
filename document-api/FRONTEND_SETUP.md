# Frontend Integration Setup Guide

## Quick Start: Connecting Your TypeScript Frontend

### Step 1: Keep Projects Separate

**Recommended Structure:**
```
your-workspace/
├── your-frontend/              # Your existing TypeScript frontend
│   ├── src/
│   ├── package.json
│   └── ...
└── fastapi-document-upload/    # Backend API (current location)
    ├── main.py
    ├── requirements.txt
    └── ...
```

**DON'T** copy the backend folder into your frontend. Keep them separate.

---

## Step 2: Add API Client to Your Frontend

### 2.1 Create API Client File

In your frontend project, create a new file for the API client:

```bash
# From your frontend directory
mkdir -p src/api
touch src/api/documentClient.ts
```

### 2.2 Copy the TypeScript Code

Open `src/api/documentClient.ts` and paste this complete API client:

```typescript
// src/api/documentClient.ts

// ============================================================================
// TypeScript Types
// ============================================================================

export interface Collection {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  document_count: number;
  created_at: string;
  updated_at: string;
}

export interface Document {
  id: string;
  user_id: string;
  collection_id: string;
  collection_name?: string; // Present when listing all documents
  original_filename: string;
  gcs_blob_name: string;
  gcs_uri: string;
  vertex_ai_doc_id: string;
  file_type: string;
  file_size_bytes: number;
  content_type: string;
  upload_date: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface CollectionListResponse {
  user_id: string;
  collections: Collection[];
  total_count: number;
  limit: number;
  offset: number;
}

export interface DocumentListResponse {
  user_id: string;
  documents: Document[];
  total_count: number;
  limit: number;
  offset: number;
}

export interface UploadResponse {
  status: string;
  message: string;
  uploaded_files: Array<{
    filename: string;
    gcs_uri: string;
    vertex_ai_doc_id: string;
    document_id: string;
  }>;
  failed_files: Array<{
    filename: string;
    error: string;
  }>;
}

export interface DeleteResponse {
  status: string;
  message: string;
  deleted: {
    documents_deleted_from_db: number;
    files_deleted_from_gcs: number;
    vertex_ai_deletions_queued: number;
  };
}

// ============================================================================
// API Client Class
// ============================================================================

export class DocumentApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  // Helper method to handle responses
  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }
    return response.json();
  }

  // ========================================
  // Collections API
  // ========================================

  async createCollection(
    userId: string,
    name: string,
    description?: string
  ): Promise<Collection> {
    const formData = new FormData();
    formData.append('user_id', userId);
    formData.append('name', name);
    if (description) formData.append('description', description);

    const response = await fetch(`${this.baseUrl}/collections`, {
      method: 'POST',
      body: formData,
    });

    return this.handleResponse<Collection>(response);
  }

  async listCollections(
    userId: string,
    limit: number = 100,
    offset: number = 0
  ): Promise<CollectionListResponse> {
    const params = new URLSearchParams({
      user_id: userId,
      limit: limit.toString(),
      offset: offset.toString(),
    });

    const response = await fetch(`${this.baseUrl}/collections?${params}`);
    return this.handleResponse<CollectionListResponse>(response);
  }

  async getCollection(collectionId: string, userId: string): Promise<Collection> {
    const params = new URLSearchParams({ user_id: userId });
    const response = await fetch(`${this.baseUrl}/collections/${collectionId}?${params}`);
    return this.handleResponse<Collection>(response);
  }

  async getCollectionDocuments(
    collectionId: string,
    userId: string,
    limit: number = 100,
    offset: number = 0
  ): Promise<DocumentListResponse> {
    const params = new URLSearchParams({
      user_id: userId,
      limit: limit.toString(),
      offset: offset.toString(),
    });

    const response = await fetch(
      `${this.baseUrl}/collections/${collectionId}/documents?${params}`
    );
    return this.handleResponse<DocumentListResponse>(response);
  }

  async deleteCollection(collectionId: string, userId: string): Promise<DeleteResponse> {
    const params = new URLSearchParams({ user_id: userId });
    const response = await fetch(
      `${this.baseUrl}/collections/${collectionId}?${params}`,
      { method: 'DELETE' }
    );
    return this.handleResponse<DeleteResponse>(response);
  }

  // ========================================
  // Documents API
  // ========================================

  async uploadDocuments(
    userId: string,
    collectionId: string,
    files: File[],
    onProgress?: (progress: number) => void
  ): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('user_id', userId);
    formData.append('collection_id', collectionId);

    files.forEach((file) => {
      formData.append('files', file);
    });

    const response = await fetch(`${this.baseUrl}/upload`, {
      method: 'POST',
      body: formData,
    });

    return this.handleResponse<UploadResponse>(response);
  }

  async listAllDocuments(
    userId: string,
    limit: number = 100,
    offset: number = 0
  ): Promise<DocumentListResponse> {
    const params = new URLSearchParams({
      user_id: userId,
      limit: limit.toString(),
      offset: offset.toString(),
    });

    const response = await fetch(`${this.baseUrl}/documents?${params}`);
    return this.handleResponse<DocumentListResponse>(response);
  }

  async deleteDocument(documentId: string, userId: string): Promise<DeleteResponse> {
    const params = new URLSearchParams({ user_id: userId });
    const response = await fetch(
      `${this.baseUrl}/documents/${documentId}?${params}`,
      { method: 'DELETE' }
    );
    return this.handleResponse<DeleteResponse>(response);
  }

  // ========================================
  // Monitoring API
  // ========================================

  async getDeletionQueueStats(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/deletion-queue/stats`);
    return this.handleResponse(response);
  }
}

// Export a default instance
export const apiClient = new DocumentApiClient();
```

### 2.3 Configure API URL

Create an environment variable file in your frontend:

```bash
# .env (for React/Vite)
VITE_API_URL=http://localhost:8000

# OR for Create React App:
# REACT_APP_API_URL=http://localhost:8000
```

Then update the client initialization:

```typescript
// src/api/documentClient.ts
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const apiClient = new DocumentApiClient(API_URL);
```

---

## Step 3: Start Both Backend and Frontend

### Terminal 1: Start Backend

```bash
cd /Users/tafadzwabwakura/Desktop/search/fastapi-document-upload
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

Backend will run at: `http://localhost:8000`

### Terminal 2: Start Frontend

```bash
cd /path/to/your-frontend
npm run dev
# or
yarn dev
```

Frontend will run at: `http://localhost:3000` (or 5173 for Vite)

---

## Step 4: Use the API Client in Your Components

### Example: React Component

```typescript
// src/components/DocumentManager.tsx
import { useState, useEffect } from 'react';
import { apiClient, Collection, Document } from '../api/documentClient';

export default function DocumentManager({ userId }: { userId: string }) {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [selectedCollection, setSelectedCollection] = useState<Collection | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);

  // Load collections on mount
  useEffect(() => {
    loadCollections();
  }, [userId]);

  const loadCollections = async () => {
    setLoading(true);
    try {
      const response = await apiClient.listCollections(userId);
      setCollections(response.collections);
    } catch (error) {
      console.error('Failed to load collections:', error);
    } finally {
      setLoading(false);
    }
  };

  const createCollection = async (name: string, description?: string) => {
    try {
      const newCollection = await apiClient.createCollection(userId, name, description);
      setCollections([...collections, newCollection]);
      return newCollection;
    } catch (error) {
      console.error('Failed to create collection:', error);
      throw error;
    }
  };

  const uploadFiles = async (files: FileList) => {
    if (!selectedCollection) {
      alert('Please select a collection first');
      return;
    }

    try {
      const response = await apiClient.uploadDocuments(
        userId,
        selectedCollection.id,
        Array.from(files)
      );

      console.log('Upload successful:', response);
      // Reload documents
      await loadDocumentsInCollection(selectedCollection.id);
    } catch (error) {
      console.error('Upload failed:', error);
    }
  };

  const loadDocumentsInCollection = async (collectionId: string) => {
    try {
      const response = await apiClient.getCollectionDocuments(collectionId, userId);
      setDocuments(response.documents);
    } catch (error) {
      console.error('Failed to load documents:', error);
    }
  };

  const deleteDocument = async (documentId: string) => {
    if (!confirm('Are you sure you want to delete this document?')) return;

    try {
      await apiClient.deleteDocument(documentId, userId);
      // Remove from local state
      setDocuments(documents.filter(doc => doc.id !== documentId));
    } catch (error) {
      console.error('Failed to delete document:', error);
    }
  };

  return (
    <div>
      <h1>Document Manager</h1>

      {/* Collections list */}
      <div>
        <h2>Collections</h2>
        {collections.map(collection => (
          <div
            key={collection.id}
            onClick={() => {
              setSelectedCollection(collection);
              loadDocumentsInCollection(collection.id);
            }}
          >
            {collection.name} ({collection.document_count} documents)
          </div>
        ))}

        <button onClick={() => {
          const name = prompt('Collection name:');
          if (name) createCollection(name);
        }}>
          Create Collection
        </button>
      </div>

      {/* File upload */}
      {selectedCollection && (
        <div>
          <h2>Upload to: {selectedCollection.name}</h2>
          <input
            type="file"
            multiple
            onChange={(e) => e.target.files && uploadFiles(e.target.files)}
          />
        </div>
      )}

      {/* Documents list */}
      <div>
        <h2>Documents</h2>
        {documents.map(doc => (
          <div key={doc.id}>
            {doc.original_filename}
            <button onClick={() => deleteDocument(doc.id)}>Delete</button>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## CORS Configuration

The backend has been configured to accept requests from:
- `http://localhost:3000` (React default)
- `http://localhost:5173` (Vite default)
- `http://localhost:4200` (Angular default)

**If your frontend runs on a different port**, update `main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:YOUR_PORT",  # Add your port here
    ],
    # ...
)
```

---

## Testing the Integration

### 1. Test Backend is Running

Visit: http://localhost:8000/docs

You should see the FastAPI interactive documentation.

### 2. Test from Frontend

```typescript
// In your browser console or a test file
import { apiClient } from './api/documentClient';

// Test creating a collection
const collection = await apiClient.createCollection('user-123', 'Test Collection');
console.log(collection);

// Test listing collections
const collections = await apiClient.listCollections('user-123');
console.log(collections);
```

---

## Common Issues

### CORS Errors
**Error:** "Access to fetch... has been blocked by CORS policy"

**Fix:** Make sure:
1. Your frontend URL is in the `allow_origins` list in `main.py`
2. Backend server is running
3. You're using the correct API URL

### Connection Refused
**Error:** "Failed to fetch" or "Connection refused"

**Fix:** Backend is not running. Start it with:
```bash
cd /Users/tafadzwabwakura/Desktop/search/fastapi-document-upload
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

### Authentication/User ID
The API currently uses a simple `user_id` string parameter. In production, you should:
1. Implement proper authentication (JWT, OAuth, etc.)
2. Get `userId` from your auth system
3. Pass it from your frontend to the API client

---

## Next Steps

1. **Copy the API client code** to your frontend (`src/api/documentClient.ts`)
2. **Start both servers** (backend on :8000, frontend on your port)
3. **Test the connection** using browser console
4. **Build your UI** using the API client methods
5. **Review DEPLOYMENT.md** when ready for production

For more detailed examples and advanced usage, see:
- `TYPESCRIPT_INTEGRATION.md` - Complete TypeScript integration guide
- `DEPLOYMENT.md` - Production deployment guide
