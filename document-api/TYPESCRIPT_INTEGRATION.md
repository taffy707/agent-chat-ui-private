# TypeScript Frontend Integration Guide

## TypeScript API Client with Full Type Safety

Your FastAPI backend is running on: `http://localhost:8000`

---

## Step 1: Define TypeScript Types

Create `types/api.ts`:

```typescript
// types/api.ts

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

export interface CollectionsResponse {
  user_id: string;
  total_count: number;
  limit: number;
  offset: number;
  returned_count: number;
  collections: Collection[];
}

export interface DocumentsResponse {
  collection_id?: string;
  collection_name?: string;
  user_id: string;
  total_count: number;
  limit: number;
  offset: number;
  returned_count: number;
  documents: Document[];
}

export interface UploadResponse {
  status: string;
  message: string;
  collection_id: string;
  collection_name: string;
  documents: {
    original_filename: string;
    document_id: string;
    gcs_uri: string;
    gcs_blob_name: string;
    size_bytes: number;
    content_type: string;
    file_type: string;
    db_id: string;
  }[];
  vertex_ai_import: {
    triggered: boolean;
    operation_name: string | null;
    status_message: string;
  };
}

export interface DeleteCollectionResponse {
  status: string;
  message: string;
  deleted: {
    collection_id: string;
    collection_name: string;
    documents_deleted_from_db: number;
    files_deleted_from_gcs: number;
    vertex_ai_deletions_queued: number;
  };
}

export interface DeleteDocumentResponse {
  status: string;
  message: string;
  deleted: {
    document_id: string;
    original_filename: string;
    gcs_blob_name: string;
    vertex_ai_doc_id: string;
  };
}

export interface ApiError {
  detail: string;
}
```

---

## Step 2: Create API Client

Create `lib/apiClient.ts`:

```typescript
// lib/apiClient.ts

import {
  Collection,
  CollectionsResponse,
  Document,
  DocumentsResponse,
  UploadResponse,
  DeleteCollectionResponse,
  DeleteDocumentResponse,
  ApiError,
} from "@/types/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(
        error.detail || `HTTP ${response.status}: ${response.statusText}`,
      );
    }
    return response.json();
  }

  // ============================================================
  // Collection Management
  // ============================================================

  async createCollection(
    userId: string,
    name: string,
    description?: string,
  ): Promise<Collection> {
    const formData = new FormData();
    formData.append("user_id", userId);
    formData.append("name", name);
    if (description) formData.append("description", description);

    const response = await fetch(`${this.baseUrl}/collections`, {
      method: "POST",
      body: formData,
    });

    return this.handleResponse<Collection>(response);
  }

  async listCollections(
    userId: string,
    options?: { limit?: number; offset?: number },
  ): Promise<CollectionsResponse> {
    const params = new URLSearchParams({
      user_id: userId,
      limit: (options?.limit ?? 100).toString(),
      offset: (options?.offset ?? 0).toString(),
    });

    const response = await fetch(`${this.baseUrl}/collections?${params}`);
    return this.handleResponse<CollectionsResponse>(response);
  }

  async getCollection(
    collectionId: string,
    userId: string,
  ): Promise<Collection> {
    const params = new URLSearchParams({ user_id: userId });
    const response = await fetch(
      `${this.baseUrl}/collections/${collectionId}?${params}`,
    );
    return this.handleResponse<Collection>(response);
  }

  async deleteCollection(
    collectionId: string,
    userId: string,
  ): Promise<DeleteCollectionResponse> {
    const params = new URLSearchParams({ user_id: userId });
    const response = await fetch(
      `${this.baseUrl}/collections/${collectionId}?${params}`,
      { method: "DELETE" },
    );
    return this.handleResponse<DeleteCollectionResponse>(response);
  }

  // ============================================================
  // Document Management
  // ============================================================

  async uploadDocuments(
    userId: string,
    collectionId: string,
    files: File[],
  ): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append("user_id", userId);
    formData.append("collection_id", collectionId);

    files.forEach((file) => {
      formData.append("files", file);
    });

    const response = await fetch(`${this.baseUrl}/upload`, {
      method: "POST",
      body: formData,
    });

    return this.handleResponse<UploadResponse>(response);
  }

  async listCollectionDocuments(
    collectionId: string,
    userId: string,
    options?: { limit?: number; offset?: number },
  ): Promise<DocumentsResponse> {
    const params = new URLSearchParams({
      user_id: userId,
      limit: (options?.limit ?? 100).toString(),
      offset: (options?.offset ?? 0).toString(),
    });

    const response = await fetch(
      `${this.baseUrl}/collections/${collectionId}/documents?${params}`,
    );
    return this.handleResponse<DocumentsResponse>(response);
  }

  async listAllDocuments(
    userId: string,
    options?: { limit?: number; offset?: number; status?: string },
  ): Promise<DocumentsResponse> {
    const params = new URLSearchParams({
      user_id: userId,
      limit: (options?.limit ?? 100).toString(),
      offset: (options?.offset ?? 0).toString(),
    });

    if (options?.status) {
      params.append("status", options.status);
    }

    const response = await fetch(`${this.baseUrl}/documents?${params}`);
    return this.handleResponse<DocumentsResponse>(response);
  }

  async deleteDocument(
    documentId: string,
    userId: string,
  ): Promise<DeleteDocumentResponse> {
    const params = new URLSearchParams({ user_id: userId });
    const response = await fetch(
      `${this.baseUrl}/documents/${documentId}?${params}`,
      { method: "DELETE" },
    );
    return this.handleResponse<DeleteDocumentResponse>(response);
  }

  // ============================================================
  // Health & Monitoring
  // ============================================================

  async healthCheck(): Promise<{
    status: string;
    gcp_project: string;
    datastore_id: string;
    bucket: string;
  }> {
    const response = await fetch(`${this.baseUrl}/health`);
    return this.handleResponse(response);
  }
}

// Export singleton instance
export const apiClient = new ApiClient(API_BASE_URL);
export default apiClient;
```

---

## Step 3: React/Next.js Component Example

```typescript
// components/DocumentManager.tsx

'use client'; // If using Next.js App Router

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/apiClient';
import { Collection, Document } from '@/types/api';

interface DocumentManagerProps {
  userId: string;
}

export default function DocumentManager({ userId }: DocumentManagerProps) {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [selectedCollection, setSelectedCollection] = useState<Collection | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadCollections();
  }, [userId]);

  const loadCollections = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.listCollections(userId);
      setCollections(response.collections);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load collections');
    } finally {
      setLoading(false);
    }
  };

  const createCollection = async (name: string, description?: string) => {
    try {
      setLoading(true);
      await apiClient.createCollection(userId, name, description);
      await loadCollections();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create collection');
    } finally {
      setLoading(false);
    }
  };

  const selectCollection = async (collection: Collection) => {
    try {
      setSelectedCollection(collection);
      setLoading(true);
      const response = await apiClient.listCollectionDocuments(collection.id, userId);
      setDocuments(response.documents);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const uploadFiles = async (files: FileList) => {
    if (!selectedCollection) {
      setError('Please select a collection first');
      return;
    }

    try {
      setLoading(true);
      await apiClient.uploadDocuments(userId, selectedCollection.id, Array.from(files));
      await selectCollection(selectedCollection); // Refresh documents
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload files');
    } finally {
      setLoading(false);
    }
  };

  const deleteCollection = async (collectionId: string) => {
    if (!confirm('Are you sure? This will delete ALL documents in this collection.')) {
      return;
    }

    try {
      setLoading(true);
      await apiClient.deleteCollection(collectionId, userId);
      await loadCollections();
      setSelectedCollection(null);
      setDocuments([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete collection');
    } finally {
      setLoading(false);
    }
  };

  const deleteDocument = async (documentId: string) => {
    try {
      setLoading(true);
      await apiClient.deleteDocument(documentId, userId);
      if (selectedCollection) {
        await selectCollection(selectedCollection); // Refresh documents
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete document');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Document Manager</h1>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Collections List */}
        <div className="col-span-1 border rounded p-4">
          <h2 className="text-xl font-semibold mb-4">Collections</h2>
          <button
            onClick={() => {
              const name = prompt('Collection name:');
              if (name) createCollection(name);
            }}
            className="w-full bg-blue-500 text-white px-4 py-2 rounded mb-4"
          >
            + New Collection
          </button>

          {loading && <p>Loading...</p>}

          <div className="space-y-2">
            {collections.map((collection) => (
              <div
                key={collection.id}
                onClick={() => selectCollection(collection)}
                className={`p-3 border rounded cursor-pointer hover:bg-gray-100 ${
                  selectedCollection?.id === collection.id ? 'bg-blue-50 border-blue-500' : ''
                }`}
              >
                <div className="font-medium">{collection.name}</div>
                <div className="text-sm text-gray-600">
                  {collection.document_count} documents
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteCollection(collection.id);
                  }}
                  className="text-red-500 text-sm mt-2"
                >
                  Delete
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Documents List */}
        <div className="col-span-2 border rounded p-4">
          {selectedCollection ? (
            <>
              <h2 className="text-xl font-semibold mb-4">{selectedCollection.name}</h2>

              <input
                type="file"
                multiple
                onChange={(e) => e.target.files && uploadFiles(e.target.files)}
                className="mb-4"
              />

              <div className="space-y-2">
                {documents.map((doc) => (
                  <div key={doc.id} className="p-3 border rounded flex justify-between items-center">
                    <div>
                      <div className="font-medium">{doc.original_filename}</div>
                      <div className="text-sm text-gray-600">
                        {(doc.file_size_bytes / 1024).toFixed(2)} KB • {doc.file_type}
                      </div>
                      <div className="text-xs text-gray-500">
                        {new Date(doc.upload_date).toLocaleString()}
                      </div>
                    </div>
                    <button
                      onClick={() => deleteDocument(doc.id)}
                      className="text-red-500"
                    >
                      Delete
                    </button>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="text-gray-500">Select a collection to view documents</p>
          )}
        </div>
      </div>
    </div>
  );
}
```

---

## Step 4: React Hooks for State Management

```typescript
// hooks/useCollections.ts

import { useState, useCallback } from "react";
import { apiClient } from "@/lib/apiClient";
import { Collection } from "@/types/api";

export function useCollections(userId: string) {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const loadCollections = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.listCollections(userId);
      setCollections(response.collections);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  const createCollection = useCallback(
    async (name: string, description?: string) => {
      await apiClient.createCollection(userId, name, description);
      await loadCollections();
    },
    [userId, loadCollections],
  );

  const deleteCollection = useCallback(
    async (collectionId: string) => {
      await apiClient.deleteCollection(collectionId, userId);
      await loadCollections();
    },
    [userId, loadCollections],
  );

  return {
    collections,
    loading,
    error,
    loadCollections,
    createCollection,
    deleteCollection,
  };
}
```

```typescript
// hooks/useDocuments.ts

import { useState, useCallback } from "react";
import { apiClient } from "@/lib/apiClient";
import { Document } from "@/types/api";

export function useDocuments(userId: string) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const loadDocuments = useCallback(
    async (collectionId: string) => {
      try {
        setLoading(true);
        setError(null);
        const response = await apiClient.listCollectionDocuments(
          collectionId,
          userId,
        );
        setDocuments(response.documents);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    },
    [userId],
  );

  const uploadDocuments = useCallback(
    async (collectionId: string, files: File[]) => {
      await apiClient.uploadDocuments(userId, collectionId, files);
      await loadDocuments(collectionId);
    },
    [userId, loadDocuments],
  );

  const deleteDocument = useCallback(
    async (documentId: string, collectionId: string) => {
      await apiClient.deleteDocument(documentId, userId);
      await loadDocuments(collectionId);
    },
    [userId, loadDocuments],
  );

  return {
    documents,
    loading,
    error,
    loadDocuments,
    uploadDocuments,
    deleteDocument,
  };
}
```

---

## Step 5: Environment Variables

```bash
# .env.local (for Next.js)
NEXT_PUBLIC_API_URL=http://localhost:8000

# .env.production
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

For Vite:

```bash
# .env.development
VITE_API_URL=http://localhost:8000

# .env.production
VITE_API_URL=https://api.yourdomain.com
```

Update `apiClient.ts`:

```typescript
// For Next.js
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// For Vite
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
```

---

## Step 6: CORS Setup in FastAPI

Add to `main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev
        "http://localhost:5173",  # Vite dev
        "https://yourdomain.com", # Production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Step 7: Upload with Progress (TypeScript)

```typescript
// lib/uploadWithProgress.ts

export async function uploadWithProgress(
  userId: string,
  collectionId: string,
  files: File[],
  onProgress: (progress: number) => void,
): Promise<any> {
  const formData = new FormData();
  formData.append("user_id", userId);
  formData.append("collection_id", collectionId);

  files.forEach((file) => {
    formData.append("files", file);
  });

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    xhr.upload.addEventListener("progress", (e) => {
      if (e.lengthComputable) {
        const percentComplete = (e.loaded / e.total) * 100;
        onProgress(Math.round(percentComplete));
      }
    });

    xhr.addEventListener("load", () => {
      if (xhr.status === 202) {
        resolve(JSON.parse(xhr.responseText));
      } else {
        reject(new Error(`Upload failed: ${xhr.statusText}`));
      }
    });

    xhr.addEventListener("error", () => {
      reject(new Error("Network error"));
    });

    xhr.open("POST", `${process.env.NEXT_PUBLIC_API_URL}/upload`);
    xhr.send(formData);
  });
}
```

Usage:

```typescript
const [uploadProgress, setUploadProgress] = useState(0);

await uploadWithProgress(userId, collectionId, files, (progress) => {
  setUploadProgress(progress);
});
```

---

## Quick Start Testing

1. **Start your backend**:

```bash
cd fastapi-document-upload
source venv/bin/activate
python main.py
```

2. **Create API client files**:

```bash
mkdir -p src/types src/lib
# Copy types/api.ts and lib/apiClient.ts from above
```

3. **Test connection**:

```typescript
import { apiClient } from "@/lib/apiClient";

// In your component or test
const health = await apiClient.healthCheck();
console.log(health); // Should show: { status: "healthy", ... }
```

4. **Use in components**:

```typescript
import { useCollections } from "@/hooks/useCollections";

const { collections, loadCollections } = useCollections("alice");

useEffect(() => {
  loadCollections();
}, []);
```

---

## TypeScript Advantages

✅ **Type Safety**: Catch errors at compile time
✅ **IntelliSense**: Auto-completion in your IDE
✅ **Refactoring**: Rename safely across codebase
✅ **Documentation**: Types serve as inline docs
✅ **Error Prevention**: No typos in API calls

Your TypeScript frontend will have full type safety when calling the API! 🎉
