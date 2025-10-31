// React hooks for document collections management

import { useState, useCallback } from "react";
import { documentApiClient } from "@/lib/document-api-client";
import { Collection, Document } from "@/types/document-api";

export function useDocumentCollections(userId: string) {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const loadCollections = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await documentApiClient.listCollections(userId);
      setCollections(response.collections);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  const createCollection = useCallback(
    async (name: string, description?: string) => {
      try {
        setLoading(true);
        setError(null);
        const newCollection = await documentApiClient.createCollection(
          userId,
          name,
          description
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
    [userId]
  );

  const deleteCollection = useCallback(
    async (collectionId: string) => {
      try {
        setLoading(true);
        setError(null);
        await documentApiClient.deleteCollection(collectionId, userId);
        setCollections((prev) =>
          prev.filter((col) => col.id !== collectionId)
        );
      } catch (err) {
        setError(err as Error);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [userId]
  );

  const refreshCollection = useCallback(
    async (collectionId: string) => {
      try {
        const updated = await documentApiClient.getCollection(
          collectionId,
          userId
        );
        setCollections((prev) =>
          prev.map((col) => (col.id === collectionId ? updated : col))
        );
      } catch (err) {
        console.error("Failed to refresh collection:", err);
      }
    },
    [userId]
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

export function useDocuments(userId: string) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  const loadDocuments = useCallback(
    async (collectionId: string) => {
      try {
        setLoading(true);
        setError(null);
        const response = await documentApiClient.listCollectionDocuments(
          collectionId,
          userId
        );
        setDocuments(response.documents);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    },
    [userId]
  );

  const uploadDocuments = useCallback(
    async (collectionId: string, files: File[]) => {
      try {
        setLoading(true);
        setError(null);
        setUploadProgress(0);
        const response = await documentApiClient.uploadDocuments(
          userId,
          collectionId,
          files,
          (progress) => setUploadProgress(progress)
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
    [userId, loadDocuments]
  );

  const deleteDocument = useCallback(
    async (documentId: string) => {
      try {
        setLoading(true);
        setError(null);
        await documentApiClient.deleteDocument(documentId, userId);
        setDocuments((prev) => prev.filter((doc) => doc.id !== documentId));
      } catch (err) {
        setError(err as Error);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [userId]
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
