"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { documentApiClient } from "@/lib/document-api-client";
import { Collection } from "@/types/document-api";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import { DocumentManager } from "@/components/document-manager";
import { ChevronDown, Plus, Loader2, AlertCircle, CheckCheck, X } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuCheckboxItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

interface KnowledgeBaseSelectorProps {
  userId: string;
  selectedCollectionIds: string[];
  onSelectionChange: (collectionIds: string[]) => void;
}

export function KnowledgeBaseSelector({
  userId,
  selectedCollectionIds,
  onSelectionChange,
}: KnowledgeBaseSelectorProps) {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [documentManagerOpen, setDocumentManagerOpen] = useState(false);

  // Memoize loadCollections with useCallback to avoid useEffect dependency issues
  const loadCollections = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await documentApiClient.listCollections(userId);
      setCollections(response.collections);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to load collections";
      setError(errorMessage);
      toast.error("Failed to load collections", {
        description: errorMessage,
      });
    } finally {
      setLoading(false);
    }
  }, [userId]);

  // Load collections on mount and when userId changes
  useEffect(() => {
    loadCollections();
  }, [loadCollections]);

  const toggleCollection = useCallback((collectionId: string) => {
    const isSelected = selectedCollectionIds.includes(collectionId);
    if (isSelected) {
      onSelectionChange(
        selectedCollectionIds.filter((id) => id !== collectionId)
      );
    } else {
      onSelectionChange([...selectedCollectionIds, collectionId]);
    }
  }, [selectedCollectionIds, onSelectionChange]);

  const handleSelectAll = useCallback(() => {
    onSelectionChange(collections.map((c) => c.id));
    toast.success(`Selected all ${collections.length} collections`);
  }, [collections, onSelectionChange]);

  const handleClearAll = useCallback(() => {
    onSelectionChange([]);
    toast.success("Cleared collection selection");
  }, [onSelectionChange]);

  const handleCreateNew = useCallback(() => {
    setDocumentManagerOpen(true);
  }, []);

  const handleDocumentManagerClose = useCallback(() => {
    setDocumentManagerOpen(false);
    // Refresh collections after closing document manager
    loadCollections();
  }, [loadCollections]);

  // Memoize computed values
  const selectedCount = useMemo(() => selectedCollectionIds.length, [selectedCollectionIds]);

  const selectedNames = useMemo(() =>
    collections
      .filter((c) => selectedCollectionIds.includes(c.id))
      .map((c) => c.name),
    [collections, selectedCollectionIds]
  );

  const buttonText = useMemo(() => {
    if (selectedCount === 0) return "Select Knowledge Base";
    if (selectedCount === 1) return selectedNames[0];
    return `${selectedCount} Selected`;
  }, [selectedCount, selectedNames]);

  // Loading state
  if (loading && collections.length === 0) {
    return (
      <Button
        variant="outline"
        disabled
        className="flex items-center gap-2 h-10 px-4 rounded-lg border border-gray-300 bg-white"
      >
        <Loader2 className="h-4 w-4 animate-spin" />
        <span className="font-medium">Loading...</span>
      </Button>
    );
  }

  // Error state
  if (error && collections.length === 0) {
    return (
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          className="flex items-center gap-2 h-10 px-4 rounded-lg border-red-300 bg-red-50 text-red-700 hover:bg-red-100"
          onClick={loadCollections}
        >
          <AlertCircle className="h-4 w-4" />
          <span className="font-medium hidden sm:inline">Failed to load</span>
          <span className="font-medium sm:hidden">Error</span>
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={loadCollections}
          className="h-10"
        >
          Retry
        </Button>
      </div>
    );
  }

  // No collections exist - show "Create Your Knowledge Base" button
  if (collections.length === 0) {
    return (
      <>
        <Button
          variant="outline"
          className="flex items-center gap-2 h-10 px-3 sm:px-4 rounded-lg border border-gray-300 bg-white hover:bg-gray-50 transition-colors"
          onClick={handleCreateNew}
        >
          <Plus className="h-4 w-4 flex-shrink-0" />
          <span className="font-medium text-sm sm:text-base whitespace-nowrap">
            Create Your Knowledge Base
          </span>
        </Button>

        <Sheet
          open={documentManagerOpen}
          onOpenChange={setDocumentManagerOpen}
        >
          <SheetContent side="right" className="w-full sm:max-w-4xl p-0">
            <DocumentManager
              userId={userId}
              onClose={handleDocumentManagerClose}
            />
          </SheetContent>
        </Sheet>
      </>
    );
  }

  // Collections exist - show "Select Knowledge Base" dropdown
  return (
    <>
      <DropdownMenu modal={false}>
        <DropdownMenuTrigger asChild>
          <Button
            variant="outline"
            className={cn(
              "flex items-center gap-2 h-10 px-3 sm:px-4 rounded-lg border border-gray-300 bg-white hover:bg-gray-50 transition-colors",
              selectedCount > 0 && "border-primary bg-primary/5"
            )}
          >
            <span className="font-medium text-sm sm:text-base truncate max-w-[120px] sm:max-w-[200px]">
              {buttonText}
            </span>
            <ChevronDown className="h-4 w-4 opacity-50 flex-shrink-0" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent
          align="start"
          className="w-80 max-h-[500px] overflow-y-auto"
          onCloseAutoFocus={(e) => {
            // Prevent auto-focus after closing to improve multi-select UX
            e.preventDefault();
          }}
        >
          <DropdownMenuLabel className="flex items-center justify-between">
            <span>
              Select Collections
              {selectedCount > 0 && (
                <span className="ml-2 text-xs text-muted-foreground font-normal">
                  ({selectedCount} of {collections.length})
                </span>
              )}
            </span>
          </DropdownMenuLabel>

          {/* Quick Actions */}
          {collections.length > 1 && (
            <div className="px-2 pb-2 flex gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleSelectAll}
                className="h-7 text-xs flex-1"
                disabled={selectedCount === collections.length}
              >
                <CheckCheck className="h-3 w-3 mr-1" />
                Select All
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleClearAll}
                className="h-7 text-xs flex-1"
                disabled={selectedCount === 0}
              >
                <X className="h-3 w-3 mr-1" />
                Clear
              </Button>
            </div>
          )}

          <DropdownMenuSeparator />

          {/* Collections List */}
          {collections.map((collection) => {
            const isSelected = selectedCollectionIds.includes(collection.id);
            return (
              <DropdownMenuCheckboxItem
                key={collection.id}
                checked={isSelected}
                onCheckedChange={() => toggleCollection(collection.id)}
                onSelect={(e) => {
                  // Prevent dropdown from closing on selection
                  e.preventDefault();
                }}
                className="cursor-pointer focus:bg-accent"
              >
                <div className="flex flex-col gap-0.5 py-1 flex-1 min-w-0">
                  <span className="font-medium truncate">{collection.name}</span>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span>
                      {collection.document_count} document
                      {collection.document_count !== 1 ? "s" : ""}
                    </span>
                    {collection.description && (
                      <>
                        <span>•</span>
                        <span className="truncate" title={collection.description}>
                          {collection.description}
                        </span>
                      </>
                    )}
                  </div>
                </div>
              </DropdownMenuCheckboxItem>
            );
          })}

          <DropdownMenuSeparator />

          {/* Create New Collection */}
          <div className="p-2">
            <Button
              variant="ghost"
              className="w-full justify-start h-9"
              onClick={(e) => {
                e.stopPropagation();
                handleCreateNew();
              }}
            >
              <Plus className="h-4 w-4 mr-2" />
              Create New Collection
            </Button>
          </div>

          {/* Footer Info */}
          {selectedCount > 0 && (
            <>
              <DropdownMenuSeparator />
              <div className="px-2 py-2 text-xs text-muted-foreground">
                {selectedCount === collections.length
                  ? "Searching all collections"
                  : `Searching ${selectedCount} collection${selectedCount !== 1 ? "s" : ""}`}
              </div>
            </>
          )}
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Document Manager Sheet */}
      <Sheet open={documentManagerOpen} onOpenChange={setDocumentManagerOpen}>
        <SheetContent side="right" className="w-full sm:max-w-4xl p-0">
          <DocumentManager
            userId={userId}
            onClose={handleDocumentManagerClose}
          />
        </SheetContent>
      </Sheet>
    </>
  );
}
