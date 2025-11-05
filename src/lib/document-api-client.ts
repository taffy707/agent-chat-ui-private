// API Client for Document Upload Service

import {
  Collection,
  CollectionListResponse,
  DocumentListResponse,
  UploadResponse,
  DeleteResponse,
  ApiError,
  HealthResponse,
} from "@/types/document-api";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DOCUMENT_API_URL || "http://localhost:8000";

class DocumentApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const error: ApiError = await response
        .json()
        .catch(() => ({ detail: "Unknown error" }));
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
  ): Promise<CollectionListResponse> {
    const params = new URLSearchParams({
      user_id: userId,
      limit: (options?.limit ?? 100).toString(),
      offset: (options?.offset ?? 0).toString(),
    });

    const response = await fetch(`${this.baseUrl}/collections?${params}`);
    return this.handleResponse<CollectionListResponse>(response);
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
  ): Promise<DeleteResponse> {
    const params = new URLSearchParams({ user_id: userId });
    const response = await fetch(
      `${this.baseUrl}/collections/${collectionId}?${params}`,
      { method: "DELETE" },
    );
    return this.handleResponse<DeleteResponse>(response);
  }

  // ============================================================
  // Document Management
  // ============================================================

  async uploadDocuments(
    userId: string,
    collectionId: string,
    files: File[],
    onProgress?: (progress: number) => void,
  ): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append("user_id", userId);
    formData.append("collection_id", collectionId);

    files.forEach((file) => {
      formData.append("files", file);
    });

    if (onProgress) {
      // Use XMLHttpRequest for upload progress tracking
      return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();

        xhr.upload.addEventListener("progress", (e) => {
          if (e.lengthComputable) {
            const percentComplete = Math.round((e.loaded / e.total) * 100);
            onProgress(percentComplete);
          }
        });

        xhr.addEventListener("load", () => {
          if (xhr.status === 202 || xhr.status === 200) {
            resolve(JSON.parse(xhr.responseText));
          } else {
            reject(new Error(`Upload failed: ${xhr.statusText}`));
          }
        });

        xhr.addEventListener("error", () => {
          reject(new Error("Network error"));
        });

        xhr.open("POST", `${this.baseUrl}/upload`);
        xhr.send(formData);
      });
    }

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
  ): Promise<DocumentListResponse> {
    const params = new URLSearchParams({
      user_id: userId,
      limit: (options?.limit ?? 100).toString(),
      offset: (options?.offset ?? 0).toString(),
    });

    const response = await fetch(
      `${this.baseUrl}/collections/${collectionId}/documents?${params}`,
    );
    return this.handleResponse<DocumentListResponse>(response);
  }

  async listAllDocuments(
    userId: string,
    options?: { limit?: number; offset?: number; status?: string },
  ): Promise<DocumentListResponse> {
    const params = new URLSearchParams({
      user_id: userId,
      limit: (options?.limit ?? 100).toString(),
      offset: (options?.offset ?? 0).toString(),
    });

    if (options?.status) {
      params.append("status", options.status);
    }

    const response = await fetch(`${this.baseUrl}/documents?${params}`);
    return this.handleResponse<DocumentListResponse>(response);
  }

  async deleteDocument(
    documentId: string,
    userId: string,
  ): Promise<DeleteResponse> {
    const params = new URLSearchParams({ user_id: userId });
    const response = await fetch(
      `${this.baseUrl}/documents/${documentId}?${params}`,
      { method: "DELETE" },
    );
    return this.handleResponse<DeleteResponse>(response);
  }

  // ============================================================
  // Health & Monitoring
  // ============================================================

  async healthCheck(): Promise<HealthResponse> {
    const response = await fetch(`${this.baseUrl}/health`);
    return this.handleResponse<HealthResponse>(response);
  }

  async getDeletionQueueStats(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/deletion-queue/stats`);
    return this.handleResponse(response);
  }
}

// Export singleton instance
export const documentApiClient = new DocumentApiClient(API_BASE_URL);
export default documentApiClient;
