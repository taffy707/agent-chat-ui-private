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

  /**
   * Create request headers with optional JWT authentication
   */
  private getHeaders(accessToken?: string): HeadersInit {
    const headers: HeadersInit = {};
    if (accessToken) {
      headers["Authorization"] = `Bearer ${accessToken}`;
    }
    return headers;
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
    name: string,
    description?: string,
    accessToken?: string,
  ): Promise<Collection> {
    const formData = new FormData();
    formData.append("name", name);
    if (description) formData.append("description", description);

    const response = await fetch(`${this.baseUrl}/collections`, {
      method: "POST",
      headers: this.getHeaders(accessToken),
      body: formData,
    });

    return this.handleResponse<Collection>(response);
  }

  async listCollections(options?: {
    limit?: number;
    offset?: number;
    accessToken?: string;
  }): Promise<CollectionListResponse> {
    const params = new URLSearchParams({
      limit: (options?.limit ?? 100).toString(),
      offset: (options?.offset ?? 0).toString(),
    });

    const response = await fetch(`${this.baseUrl}/collections?${params}`, {
      headers: this.getHeaders(options?.accessToken),
    });
    return this.handleResponse<CollectionListResponse>(response);
  }

  async getCollection(
    collectionId: string,
    accessToken?: string,
  ): Promise<Collection> {
    const response = await fetch(
      `${this.baseUrl}/collections/${collectionId}`,
      {
        headers: this.getHeaders(accessToken),
      },
    );
    return this.handleResponse<Collection>(response);
  }

  async deleteCollection(
    collectionId: string,
    accessToken?: string,
  ): Promise<DeleteResponse> {
    const response = await fetch(
      `${this.baseUrl}/collections/${collectionId}`,
      {
        method: "DELETE",
        headers: this.getHeaders(accessToken),
      },
    );
    return this.handleResponse<DeleteResponse>(response);
  }

  // ============================================================
  // Document Management
  // ============================================================

  async uploadDocuments(
    collectionId: string,
    files: File[],
    options?: {
      accessToken?: string;
      onProgress?: (progress: number) => void;
    },
  ): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append("collection_id", collectionId);

    files.forEach((file) => {
      formData.append("files", file);
    });

    if (options?.onProgress) {
      // Use XMLHttpRequest for upload progress tracking
      return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();

        xhr.upload.addEventListener("progress", (e) => {
          if (e.lengthComputable) {
            const percentComplete = Math.round((e.loaded / e.total) * 100);
            options.onProgress!(percentComplete);
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

        // Add Authorization header if token provided
        if (options?.accessToken) {
          xhr.setRequestHeader(
            "Authorization",
            `Bearer ${options.accessToken}`,
          );
        }

        xhr.send(formData);
      });
    }

    const response = await fetch(`${this.baseUrl}/upload`, {
      method: "POST",
      headers: this.getHeaders(options?.accessToken),
      body: formData,
    });

    return this.handleResponse<UploadResponse>(response);
  }

  async listCollectionDocuments(
    collectionId: string,
    options?: { limit?: number; offset?: number; accessToken?: string },
  ): Promise<DocumentListResponse> {
    const params = new URLSearchParams({
      limit: (options?.limit ?? 100).toString(),
      offset: (options?.offset ?? 0).toString(),
    });

    const response = await fetch(
      `${this.baseUrl}/collections/${collectionId}/documents?${params}`,
      {
        headers: this.getHeaders(options?.accessToken),
      },
    );
    return this.handleResponse<DocumentListResponse>(response);
  }

  async listAllDocuments(options?: {
    limit?: number;
    offset?: number;
    status?: string;
    accessToken?: string;
  }): Promise<DocumentListResponse> {
    const params = new URLSearchParams({
      limit: (options?.limit ?? 100).toString(),
      offset: (options?.offset ?? 0).toString(),
    });

    if (options?.status) {
      params.append("status", options.status);
    }

    const response = await fetch(`${this.baseUrl}/documents?${params}`, {
      headers: this.getHeaders(options?.accessToken),
    });
    return this.handleResponse<DocumentListResponse>(response);
  }

  async deleteDocument(
    documentId: string,
    accessToken?: string,
  ): Promise<DeleteResponse> {
    const response = await fetch(`${this.baseUrl}/documents/${documentId}`, {
      method: "DELETE",
      headers: this.getHeaders(accessToken),
    });
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
