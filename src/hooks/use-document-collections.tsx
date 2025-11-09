// React hooks for document collections management

import { useState, useCallback } from "react";
import { documentApiClient } from "@/lib/document-api-client";
import { Collection, Document } from "@/types/document-api";
import { useAuthContext } from "@/providers/Auth";

export function useDocumentCollections() {
  const { session } = useAuthContext();
  const [collections, setCollections] = useState<Collection[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const loadCollections = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const accessToken = session?.accessToken;
      if (!accessToken) {
        throw new Error("Not authenticated");
      }
      const response = await documentApiClient.listCollections({
        accessToken,
      });
      setCollections(response.collections);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, [session?.accessToken]);

  const createCollection = useCallback(
    async (name: string, description?: string) => {
      try {
        setLoading(true);
        setError(null);
        const accessToken = session?.accessToken;
        if (!accessToken) {
          throw new Error("Not authenticated");
        }
        const newCollection = await documentApiClient.createCollection(
          name,
          description,
          accessToken,
        );
        setCollections((prev) => [...prev, newCollection]);
        return newCollection;
      } catch (err) {
        setError(err as Error);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [session?.accessToken],
  );

  const deleteCollection = useCallback(
    async (collectionId: string) => {
      try {
        setLoading(true);
        setError(null);
        const accessToken = session?.accessToken;
        if (!accessToken) {
          throw new Error("Not authenticated");
        }
        await documentApiClient.deleteCollection(collectionId, accessToken);
        setCollections((prev) => prev.filter((col) => col.id !== collectionId));
      } catch (err) {
        setError(err as Error);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [session?.accessToken],
  );

  const refreshCollection = useCallback(
    async (collectionId: string) => {
      try {
        const accessToken = session?.accessToken;
        if (!accessToken) {
          throw new Error("Not authenticated");
        }
        const updated = await documentApiClient.getCollection(
          collectionId,
          accessToken,
        );
        setCollections((prev) =>
          prev.map((col) => (col.id === collectionId ? updated : col)),
        );
      } catch (err) {
        console.error("Failed to refresh collection:", err);
      }
    },
    [session?.accessToken],
  );

  return {
    collections,
    loading,
    error,
    loadCollections,
    createCollection,
    deleteCollection,
    refreshCollection,
  };
}

export function useDocuments() {
  const { session } = useAuthContext();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  const loadDocuments = useCallback(
    async (collectionId: string) => {
      try {
        setLoading(true);
        setError(null);
        const accessToken = session?.accessToken;
        if (!accessToken) {
          throw new Error("Not authenticated");
        }
        const response = await documentApiClient.listCollectionDocuments(
          collectionId,
          {
            accessToken,
          },
        );
        setDocuments(response.documents);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    },
    [session?.accessToken],
  );

  const uploadDocuments = useCallback(
    async (collectionId: string, files: File[]) => {
      try {
        setLoading(true);
        setError(null);
        setUploadProgress(0);
        const accessToken = session?.accessToken;
        if (!accessToken) {
          throw new Error("Not authenticated");
        }
        const response = await documentApiClient.uploadDocuments(
          collectionId,
          files,
          {
            accessToken,
            onProgress: (progress) => setUploadProgress(progress),
          },
        );
        // Refresh document list after upload
        await loadDocuments(collectionId);
        return response;
      } catch (err) {
        setError(err as Error);
        throw err;
      } finally {
        setLoading(false);
        setUploadProgress(0);
      }
    },
    [session?.accessToken, loadDocuments],
  );

  const deleteDocument = useCallback(
    async (documentId: string) => {
      try {
        setLoading(true);
        setError(null);
        const accessToken = session?.accessToken;
        if (!accessToken) {
          throw new Error("Not authenticated");
        }
        await documentApiClient.deleteDocument(documentId, accessToken);
        setDocuments((prev) => prev.filter((doc) => doc.id !== documentId));
      } catch (err) {
        setError(err as Error);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [session?.accessToken],
  );

  return {
    documents,
    loading,
    error,
    uploadProgress,
    loadDocuments,
    uploadDocuments,
    deleteDocument,
  };
}
