/**
 * Custom React hook for making authenticated requests to the Document API.
 * Automatically includes JWT token from Auth context in all requests.
 */

import { useAuthContext } from "@/providers/Auth";
import { documentApiClient } from "@/lib/document-api-client";
import {
  Collection,
  CollectionListResponse,
  DocumentListResponse,
  UploadResponse,
  DeleteResponse,
} from "@/types/document-api";

export function useDocumentApi() {
  const { session, isAuthenticated } = useAuthContext();

  /**
   * Get the access token from the current session
   */
  const getAccessToken = (): string | undefined => {
    return session?.accessToken ?? undefined;
  };

  /**
   * Check if user is authenticated and throw error if not
   */
  const ensureAuthenticated = () => {
    if (!isAuthenticated || !session?.accessToken) {
      throw new Error(
        "User must be authenticated to perform this action. Please sign in.",
      );
    }
  };

  // ============================================================
  // Collection Management
  // ============================================================

  /**
   * Create a new collection
   */
  const createCollection = async (
    name: string,
    description?: string,
  ): Promise<Collection> => {
    ensureAuthenticated();
    return documentApiClient.createCollection(
      name,
      description,
      getAccessToken(),
    );
  };

  /**
   * List all collections for the authenticated user
   */
  const listCollections = async (options?: {
    limit?: number;
    offset?: number;
  }): Promise<CollectionListResponse> => {
    ensureAuthenticated();
    return documentApiClient.listCollections({
      ...options,
      accessToken: getAccessToken(),
    });
  };

  /**
   * Get a specific collection by ID
   */
  const getCollection = async (collectionId: string): Promise<Collection> => {
    ensureAuthenticated();
    return documentApiClient.getCollection(collectionId, getAccessToken());
  };

  /**
   * Delete a collection and all its documents
   */
  const deleteCollection = async (
    collectionId: string,
  ): Promise<DeleteResponse> => {
    ensureAuthenticated();
    return documentApiClient.deleteCollection(collectionId, getAccessToken());
  };

  // ============================================================
  // Document Management
  // ============================================================

  /**
   * Upload documents to a collection
   */
  const uploadDocuments = async (
    collectionId: string,
    files: File[],
    onProgress?: (progress: number) => void,
  ): Promise<UploadResponse> => {
    ensureAuthenticated();
    return documentApiClient.uploadDocuments(collectionId, files, {
      accessToken: getAccessToken(),
      onProgress,
    });
  };

  /**
   * List documents in a specific collection
   */
  const listCollectionDocuments = async (
    collectionId: string,
    options?: { limit?: number; offset?: number },
  ): Promise<DocumentListResponse> => {
    ensureAuthenticated();
    return documentApiClient.listCollectionDocuments(collectionId, {
      ...options,
      accessToken: getAccessToken(),
    });
  };

  /**
   * List all documents for the authenticated user
   */
  const listAllDocuments = async (options?: {
    limit?: number;
    offset?: number;
    status?: string;
  }): Promise<DocumentListResponse> => {
    ensureAuthenticated();
    return documentApiClient.listAllDocuments({
      ...options,
      accessToken: getAccessToken(),
    });
  };

  /**
   * Delete a document
   */
  const deleteDocument = async (
    documentId: string,
  ): Promise<DeleteResponse> => {
    ensureAuthenticated();
    return documentApiClient.deleteDocument(documentId, getAccessToken());
  };

  // ============================================================
  // Health & Monitoring (Public endpoints)
  // ============================================================

  /**
   * Check API health status (no authentication required)
   */
  const healthCheck = () => {
    return documentApiClient.healthCheck();
  };

  /**
   * Get deletion queue statistics (no authentication required)
   */
  const getDeletionQueueStats = () => {
    return documentApiClient.getDeletionQueueStats();
  };

  return {
    // Auth state
    isAuthenticated,
    accessToken: getAccessToken(),

    // Collection operations
    createCollection,
    listCollections,
    getCollection,
    deleteCollection,

    // Document operations
    uploadDocuments,
    listCollectionDocuments,
    listAllDocuments,
    deleteDocument,

    // Monitoring
    healthCheck,
    getDeletionQueueStats,
  };
}
