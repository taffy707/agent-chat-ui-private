/**
 * Example Component: Document Upload with Authentication
 *
 * This file demonstrates how to use the Document API with JWT authentication
 * in your React components. Copy and adapt this code for your needs.
 *
 * IMPORTANT: This is an example file - not part of the actual application.
 * Place this component in your app directory when you're ready to use it.
 */

"use client";

import { useState } from "react";
import { useDocumentApi } from "@/hooks/useDocumentApi";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import type { Collection } from "@/types/document-api";

export function DocumentUploadExample() {
  const {
    isAuthenticated,
    createCollection,
    listCollections,
    uploadDocuments,
    listAllDocuments,
    deleteDocument,
  } = useDocumentApi();

  const [collections, setCollections] = useState<Collection[]>([]);
  const [selectedCollectionId, setSelectedCollectionId] = useState<
    string | null
  >(null);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [isLoading, setIsLoading] = useState(false);

  // ============================================================
  // Example 1: Create a New Collection
  // ============================================================
  const handleCreateCollection = async () => {
    if (!isAuthenticated) {
      toast.error("Please sign in to create collections");
      return;
    }

    try {
      setIsLoading(true);
      const collection = await createCollection(
        "My Documents",
        "Personal document collection",
      );

      toast.success(`Collection "${collection.name}" created!`);
      console.log("Created collection:", collection);

      // Refresh collections list
      await handleListCollections();
    } catch (error) {
      console.error("Failed to create collection:", error);
      toast.error(
        error instanceof Error ? error.message : "Failed to create collection",
      );
    } finally {
      setIsLoading(false);
    }
  };

  // ============================================================
  // Example 2: List All Collections
  // ============================================================
  const handleListCollections = async () => {
    if (!isAuthenticated) {
      toast.error("Please sign in to view collections");
      return;
    }

    try {
      setIsLoading(true);
      const response = await listCollections({ limit: 50, offset: 0 });

      setCollections(response.collections);
      console.log("Collections:", response);

      toast.success(`Loaded ${response.collections.length} collections`);
    } catch (error) {
      console.error("Failed to list collections:", error);
      toast.error(
        error instanceof Error ? error.message : "Failed to load collections",
      );
    } finally {
      setIsLoading(false);
    }
  };

  // ============================================================
  // Example 3: Upload Documents with Progress Tracking
  // ============================================================
  const handleFileUpload = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    if (!isAuthenticated) {
      toast.error("Please sign in to upload documents");
      return;
    }

    if (!selectedCollectionId) {
      toast.error("Please select a collection first");
      return;
    }

    const files = Array.from(event.target.files || []);
    if (files.length === 0) return;

    try {
      setIsLoading(true);
      setUploadProgress(0);

      // Upload with progress tracking
      const result = await uploadDocuments(
        selectedCollectionId,
        files,
        (progress) => {
          setUploadProgress(progress);
          console.log(`Upload progress: ${progress}%`);
        },
      );

      console.log("Upload result:", result);
      toast.success(
        `Successfully uploaded ${result.documents.length} document(s)`,
      );

      // Optionally list documents after upload
      await handleListDocuments();
    } catch (error) {
      console.error("Failed to upload documents:", error);
      toast.error(
        error instanceof Error ? error.message : "Failed to upload documents",
      );
    } finally {
      setIsLoading(false);
      setUploadProgress(0);
      event.target.value = ""; // Reset file input
    }
  };

  // ============================================================
  // Example 4: List All Documents
  // ============================================================
  const handleListDocuments = async () => {
    if (!isAuthenticated) {
      toast.error("Please sign in to view documents");
      return;
    }

    try {
      setIsLoading(true);
      const response = await listAllDocuments({
        limit: 100,
        offset: 0,
      });

      console.log("Documents:", response);
      toast.success(`Loaded ${response.documents.length} documents`);
    } catch (error) {
      console.error("Failed to list documents:", error);
      toast.error(
        error instanceof Error ? error.message : "Failed to load documents",
      );
    } finally {
      setIsLoading(false);
    }
  };

  // ============================================================
  // Example 5: Delete a Document
  // ============================================================
  const handleDeleteDocument = async (documentId: string) => {
    if (!isAuthenticated) {
      toast.error("Please sign in to delete documents");
      return;
    }

    if (!confirm("Are you sure you want to delete this document?")) {
      return;
    }

    try {
      setIsLoading(true);
      const result = await deleteDocument(documentId);

      console.log("Delete result:", result);
      toast.success("Document deleted successfully");

      // Refresh documents list
      await handleListDocuments();
    } catch (error) {
      console.error("Failed to delete document:", error);
      toast.error(
        error instanceof Error ? error.message : "Failed to delete document",
      );
    } finally {
      setIsLoading(false);
    }
  };

  // ============================================================
  // Render UI
  // ============================================================

  if (!isAuthenticated) {
    return (
      <div className="p-8 text-center">
        <p className="text-muted-foreground mb-4">
          Please sign in to manage documents
        </p>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold mb-2">Document Management</h1>
        <p className="text-muted-foreground">
          Upload and manage your documents with JWT authentication
        </p>
      </div>

      {/* Example 1 & 2: Create and List Collections */}
      <div className="space-y-4 border rounded-lg p-4">
        <h2 className="text-lg font-semibold">Collections</h2>

        <div className="flex gap-2">
          <Button onClick={handleCreateCollection} disabled={isLoading}>
            Create Example Collection
          </Button>
          <Button
            onClick={handleListCollections}
            variant="outline"
            disabled={isLoading}
          >
            Refresh Collections
          </Button>
        </div>

        {collections.length > 0 && (
          <div className="space-y-2">
            <p className="text-sm font-medium">Select a collection:</p>
            <select
              className="w-full p-2 border rounded"
              value={selectedCollectionId || ""}
              onChange={(e) => setSelectedCollectionId(e.target.value)}
            >
              <option value="">-- Select Collection --</option>
              {collections.map((col) => (
                <option key={col.id} value={col.id}>
                  {col.name} ({col.document_count} documents)
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Example 3: Upload Documents */}
      <div className="space-y-4 border rounded-lg p-4">
        <h2 className="text-lg font-semibold">Upload Documents</h2>

        <div className="space-y-2">
          <Input
            type="file"
            multiple
            accept=".pdf,.docx,.txt,.html,.htm"
            onChange={handleFileUpload}
            disabled={isLoading || !selectedCollectionId}
          />

          {uploadProgress > 0 && (
            <div className="space-y-1">
              <div className="flex justify-between text-sm">
                <span>Uploading...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

          {!selectedCollectionId && (
            <p className="text-sm text-muted-foreground">
              Please select a collection first
            </p>
          )}
        </div>
      </div>

      {/* Example 4: List Documents */}
      <div className="space-y-4 border rounded-lg p-4">
        <h2 className="text-lg font-semibold">Documents</h2>

        <Button onClick={handleListDocuments} disabled={isLoading}>
          List All Documents
        </Button>

        <p className="text-sm text-muted-foreground">
          Check browser console to see the results
        </p>
      </div>

      {/* Loading indicator */}
      {isLoading && (
        <div className="text-center text-sm text-muted-foreground">
          Loading...
        </div>
      )}
    </div>
  );
}

/**
 * ============================================================
 * USAGE EXAMPLES (Code Snippets)
 * ============================================================
 */

/*
// Example 1: Simple component that creates a collection
export function CreateCollectionButton() {
  const { createCollection, isAuthenticated } = useDocumentApi();

  const handleClick = async () => {
    if (!isAuthenticated) {
      alert("Please sign in first");
      return;
    }

    try {
      const collection = await createCollection("My Collection", "Description");
      console.log("Created:", collection);
    } catch (error) {
      console.error("Error:", error);
    }
  };

  return <button onClick={handleClick}>Create Collection</button>;
}

// Example 2: Upload documents with async/await
async function uploadMyDocuments(files: File[], collectionId: string) {
  const { uploadDocuments } = useDocumentApi();

  try {
    const result = await uploadDocuments(collectionId, files, (progress) => {
      console.log(`Upload: ${progress}%`);
    });

    console.log("Uploaded documents:", result.documents);
    return result;
  } catch (error) {
    console.error("Upload failed:", error);
    throw error;
  }
}

// Example 3: Fetch and display collections
export function CollectionsList() {
  const { listCollections } = useDocumentApi();
  const [collections, setCollections] = useState([]);

  useEffect(() => {
    const loadCollections = async () => {
      try {
        const response = await listCollections({ limit: 50 });
        setCollections(response.collections);
      } catch (error) {
        console.error("Failed to load collections:", error);
      }
    };

    loadCollections();
  }, [listCollections]);

  return (
    <ul>
      {collections.map((col) => (
        <li key={col.id}>
          {col.name} - {col.document_count} documents
        </li>
      ))}
    </ul>
  );
}

// Example 4: Delete document with confirmation
async function deleteDocumentWithConfirmation(documentId: string) {
  const { deleteDocument } = useDocumentApi();

  if (!confirm("Delete this document?")) {
    return;
  }

  try {
    const result = await deleteDocument(documentId);
    console.log("Deleted:", result);
    alert("Document deleted successfully");
  } catch (error) {
    console.error("Delete failed:", error);
    alert("Failed to delete document");
  }
}

// Example 5: Check authentication status
export function DocumentFeature() {
  const { isAuthenticated, accessToken } = useDocumentApi();

  if (!isAuthenticated) {
    return <div>Please sign in to access document features</div>;
  }

  return (
    <div>
      <p>Authenticated with token: {accessToken?.substring(0, 20)}...</p>
      // Your document management UI here
    </div>
  );
}
*/
