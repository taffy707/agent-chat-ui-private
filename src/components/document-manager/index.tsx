"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";
import {
  useDocumentCollections,
  useDocuments,
} from "@/hooks/use-document-collections";
import {
  Upload,
  Trash2,
  FolderPlus,
  Folder,
  FileText,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Clock,
} from "lucide-react";
import { Collection } from "@/types/document-api";
import { cn } from "@/lib/utils";

interface DocumentManagerProps {
  userId: string;
  onClose?: () => void;
}

export function DocumentManager({ userId, onClose }: DocumentManagerProps) {
  const {
    collections,
    loading: collectionsLoading,
    error: collectionsError,
    loadCollections,
    createCollection,
    deleteCollection,
    refreshCollection,
  } = useDocumentCollections();

  const {
    documents,
    loading: documentsLoading,
    uploadProgress,
    loadDocuments,
    uploadDocuments,
    deleteDocument,
  } = useDocuments();

  const [selectedCollection, setSelectedCollection] =
    useState<Collection | null>(null);
  const [newCollectionName, setNewCollectionName] = useState("");
  const [showNewCollectionForm, setShowNewCollectionForm] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);

  // Load collections on mount
  useEffect(() => {
    loadCollections();
  }, [loadCollections]);

  // Load documents when collection is selected
  useEffect(() => {
    if (selectedCollection) {
      loadDocuments(selectedCollection.id);
    }
  }, [selectedCollection, loadDocuments]);

  const handleCreateCollection = async () => {
    if (!newCollectionName.trim()) {
      toast.error("Please enter a collection name");
      return;
    }

    try {
      const newCollection = await createCollection(newCollectionName);
      toast.success(`Collection "${newCollectionName}" created`);
      setNewCollectionName("");
      setShowNewCollectionForm(false);
      setSelectedCollection(newCollection);
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to create collection",
      );
    }
  };

  const handleDeleteCollection = async (collectionId: string) => {
    if (
      !confirm(
        "Are you sure? This will delete ALL documents in this collection.",
      )
    ) {
      return;
    }

    try {
      await deleteCollection(collectionId);
      toast.success("Collection deleted");
      if (selectedCollection?.id === collectionId) {
        setSelectedCollection(null);
      }
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to delete collection",
      );
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSelectedFiles(e.target.files);
  };

  const handleUpload = async () => {
    if (!selectedCollection) {
      toast.error("Please select a collection first");
      return;
    }

    if (!selectedFiles || selectedFiles.length === 0) {
      toast.error("Please select files to upload");
      return;
    }

    try {
      const filesArray = Array.from(selectedFiles);
      const response = await uploadDocuments(selectedCollection.id, filesArray);
      toast.success(
        `Uploaded ${response.documents.length} file(s) successfully`,
      );
      setSelectedFiles(null);
      // Refresh collection to update document count
      await refreshCollection(selectedCollection.id);
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to upload files",
      );
    }
  };

  const handleDeleteDocument = async (documentId: string, filename: string) => {
    if (!confirm(`Delete "${filename}"?`)) {
      return;
    }

    try {
      await deleteDocument(documentId);
      toast.success("Document deleted");
      if (selectedCollection) {
        await refreshCollection(selectedCollection.id);
      }
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to delete document",
      );
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + " KB";
    return (bytes / (1024 * 1024)).toFixed(2) + " MB";
  };

  const getIndexStatusBadge = (indexStatus: string) => {
    switch (indexStatus) {
      case "indexing":
      case "pending":
        return (
          <span className="inline-flex items-center gap-1 rounded bg-amber-50 px-2 py-1 text-xs text-amber-600">
            <Clock className="h-3 w-3 animate-pulse" />
            Processing...
          </span>
        );
      case "indexed":
        return (
          <span className="inline-flex items-center gap-1 rounded bg-green-50 px-2 py-1 text-xs text-green-600">
            <CheckCircle2 className="h-3 w-3" />
            Ready
          </span>
        );
      case "failed":
        return (
          <span className="inline-flex items-center gap-1 rounded bg-red-50 px-2 py-1 text-xs text-red-600">
            <AlertCircle className="h-3 w-3" />
            Failed
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div className="flex h-full flex-col">
      <div className="border-b p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">Document Manager</h2>
          {onClose && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
            >
              Close
            </Button>
          )}
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Collections Sidebar */}
        <div className="flex w-64 flex-col border-r">
          <div className="border-b p-4">
            <Button
              variant="outline"
              size="sm"
              className="w-full"
              onClick={() => setShowNewCollectionForm(!showNewCollectionForm)}
            >
              <FolderPlus className="mr-2 h-4 w-4" />
              New Collection
            </Button>
          </div>

          {showNewCollectionForm && (
            <div className="bg-muted/50 border-b p-4">
              <Label htmlFor="collection-name">Collection Name</Label>
              <Input
                id="collection-name"
                value={newCollectionName}
                onChange={(e) => setNewCollectionName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleCreateCollection()}
                placeholder="Enter name..."
                className="mt-2"
              />
              <div className="mt-2 flex gap-2">
                <Button
                  size="sm"
                  onClick={handleCreateCollection}
                >
                  Create
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => {
                    setShowNewCollectionForm(false);
                    setNewCollectionName("");
                  }}
                >
                  Cancel
                </Button>
              </div>
            </div>
          )}

          <div className="flex-1 overflow-y-auto p-2">
            {collectionsLoading && (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            )}

            {collectionsError && (
              <div className="p-4 text-sm text-red-600">
                Error loading collections
              </div>
            )}

            {!collectionsLoading && collections.length === 0 && (
              <div className="text-muted-foreground p-4 text-center text-sm">
                No collections yet. Create one to get started.
              </div>
            )}

            <div className="space-y-1">
              {collections.map((collection) => (
                <div
                  key={collection.id}
                  className={cn(
                    "group hover:bg-muted relative cursor-pointer rounded-md p-3 transition-colors",
                    selectedCollection?.id === collection.id &&
                      "bg-muted border-border border",
                  )}
                  onClick={() => setSelectedCollection(collection)}
                >
                  <div className="flex items-start justify-between">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <Folder className="h-4 w-4 flex-shrink-0" />
                        <span className="truncate text-sm font-medium">
                          {collection.name}
                        </span>
                      </div>
                      <div className="text-muted-foreground mt-1 text-xs">
                        {collection.document_count} document
                        {collection.document_count !== 1 ? "s" : ""}
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteCollection(collection.id);
                      }}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Documents Area */}
        <div className="flex flex-1 flex-col">
          {selectedCollection ? (
            <>
              <div className="border-b p-4">
                <h3 className="mb-4 font-semibold">
                  {selectedCollection.name}
                </h3>

                {/* Upload Area */}
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base">
                      Upload Documents
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <Input
                        type="file"
                        multiple
                        accept=".pdf,.docx,.txt,.html,.htm"
                        onChange={handleFileSelect}
                      />
                      {selectedFiles && selectedFiles.length > 0 && (
                        <div className="text-muted-foreground text-sm">
                          {selectedFiles.length} file(s) selected
                        </div>
                      )}
                      {uploadProgress > 0 && uploadProgress < 100 && (
                        <div className="space-y-2">
                          <div className="text-muted-foreground text-sm">
                            Uploading: {uploadProgress}%
                          </div>
                          <div className="bg-muted h-2 w-full rounded-full">
                            <div
                              className="bg-primary h-2 rounded-full transition-all"
                              style={{ width: `${uploadProgress}%` }}
                            />
                          </div>
                        </div>
                      )}
                      <Button
                        onClick={handleUpload}
                        disabled={
                          !selectedFiles ||
                          selectedFiles.length === 0 ||
                          documentsLoading
                        }
                      >
                        {documentsLoading ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Uploading...
                          </>
                        ) : (
                          <>
                            <Upload className="mr-2 h-4 w-4" />
                            Upload Files
                          </>
                        )}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Documents List */}
              <div className="flex-1 overflow-y-auto p-4">
                {documentsLoading && documents.length === 0 ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin" />
                  </div>
                ) : documents.length === 0 ? (
                  <div className="text-muted-foreground py-8 text-center">
                    No documents in this collection yet. Upload some files to
                    get started.
                  </div>
                ) : (
                  <div className="space-y-2">
                    {documents.map((doc) => {
                      const isIndexing =
                        doc.index_status === "indexing" ||
                        doc.index_status === "pending";
                      return (
                        <Card key={doc.id}>
                          <CardContent className="p-4">
                            <div className="flex items-start justify-between">
                              <div className="flex flex-1 items-start gap-3">
                                <FileText className="mt-0.5 h-5 w-5 flex-shrink-0" />
                                <div className="min-w-0 flex-1">
                                  <div className="flex items-center gap-2">
                                    <div className="truncate font-medium">
                                      {doc.original_filename}
                                    </div>
                                    {getIndexStatusBadge(doc.index_status)}
                                  </div>
                                  <div className="text-muted-foreground mt-1 text-sm">
                                    {formatFileSize(doc.file_size_bytes)} •{" "}
                                    {doc.file_type}
                                  </div>
                                  <div className="text-muted-foreground mt-1 text-xs">
                                    {new Date(doc.upload_date).toLocaleString()}
                                  </div>
                                </div>
                              </div>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() =>
                                  handleDeleteDocument(
                                    doc.id,
                                    doc.original_filename,
                                  )
                                }
                                disabled={isIndexing}
                                title={
                                  isIndexing
                                    ? "Cannot delete while document is being processed"
                                    : "Delete document"
                                }
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </CardContent>
                        </Card>
                      );
                    })}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="text-muted-foreground flex h-full items-center justify-center">
              Select a collection to view documents
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
