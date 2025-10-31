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
  } = useDocumentCollections(userId);

  const {
    documents,
    loading: documentsLoading,
    uploadProgress,
    loadDocuments,
    uploadDocuments,
    deleteDocument,
  } = useDocuments(userId);

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
        error instanceof Error
          ? error.message
          : "Failed to create collection"
      );
    }
  };

  const handleDeleteCollection = async (collectionId: string) => {
    if (!confirm("Are you sure? This will delete ALL documents in this collection.")) {
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
        error instanceof Error ? error.message : "Failed to delete collection"
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
      const response = await uploadDocuments(
        selectedCollection.id,
        filesArray
      );
      toast.success(
        `Uploaded ${response.documents.length} file(s) successfully`
      );
      setSelectedFiles(null);
      // Refresh collection to update document count
      await refreshCollection(selectedCollection.id);
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to upload files"
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
        error instanceof Error ? error.message : "Failed to delete document"
      );
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + " KB";
    return (bytes / (1024 * 1024)).toFixed(2) + " MB";
  };

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">Document Manager</h2>
          {onClose && (
            <Button variant="ghost" size="sm" onClick={onClose}>
              Close
            </Button>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-hidden flex">
        {/* Collections Sidebar */}
        <div className="w-64 border-r flex flex-col">
          <div className="p-4 border-b">
            <Button
              variant="outline"
              size="sm"
              className="w-full"
              onClick={() => setShowNewCollectionForm(!showNewCollectionForm)}
            >
              <FolderPlus className="h-4 w-4 mr-2" />
              New Collection
            </Button>
          </div>

          {showNewCollectionForm && (
            <div className="p-4 border-b bg-muted/50">
              <Label htmlFor="collection-name">Collection Name</Label>
              <Input
                id="collection-name"
                value={newCollectionName}
                onChange={(e) => setNewCollectionName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleCreateCollection()}
                placeholder="Enter name..."
                className="mt-2"
              />
              <div className="flex gap-2 mt-2">
                <Button size="sm" onClick={handleCreateCollection}>
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
              <div className="p-4 text-sm text-muted-foreground text-center">
                No collections yet. Create one to get started.
              </div>
            )}

            <div className="space-y-1">
              {collections.map((collection) => (
                <div
                  key={collection.id}
                  className={cn(
                    "group relative p-3 rounded-md cursor-pointer hover:bg-muted transition-colors",
                    selectedCollection?.id === collection.id &&
                      "bg-muted border border-border"
                  )}
                  onClick={() => setSelectedCollection(collection)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <Folder className="h-4 w-4 flex-shrink-0" />
                        <span className="font-medium text-sm truncate">
                          {collection.name}
                        </span>
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        {collection.document_count} document
                        {collection.document_count !== 1 ? "s" : ""}
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="opacity-0 group-hover:opacity-100 h-6 w-6 p-0"
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
        <div className="flex-1 flex flex-col">
          {selectedCollection ? (
            <>
              <div className="p-4 border-b">
                <h3 className="font-semibold mb-4">
                  {selectedCollection.name}
                </h3>

                {/* Upload Area */}
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base">Upload Documents</CardTitle>
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
                        <div className="text-sm text-muted-foreground">
                          {selectedFiles.length} file(s) selected
                        </div>
                      )}
                      {uploadProgress > 0 && uploadProgress < 100 && (
                        <div className="space-y-2">
                          <div className="text-sm text-muted-foreground">
                            Uploading: {uploadProgress}%
                          </div>
                          <div className="w-full bg-muted rounded-full h-2">
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
                  <div className="text-center py-8 text-muted-foreground">
                    No documents in this collection yet. Upload some files to
                    get started.
                  </div>
                ) : (
                  <div className="space-y-2">
                    {documents.map((doc) => (
                      <Card key={doc.id}>
                        <CardContent className="p-4">
                          <div className="flex items-start justify-between">
                            <div className="flex items-start gap-3 flex-1">
                              <FileText className="h-5 w-5 mt-0.5 flex-shrink-0" />
                              <div className="flex-1 min-w-0">
                                <div className="font-medium truncate">
                                  {doc.original_filename}
                                </div>
                                <div className="text-sm text-muted-foreground mt-1">
                                  {formatFileSize(doc.file_size_bytes)} •{" "}
                                  {doc.file_type} • {doc.status}
                                </div>
                                <div className="text-xs text-muted-foreground mt-1">
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
                                  doc.original_filename
                                )
                              }
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-full text-muted-foreground">
              Select a collection to view documents
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
