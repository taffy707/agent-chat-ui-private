"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { documentApiClient } from "@/lib/document-api-client";
import { Collection } from "@/types/document-api";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import { DocumentManager } from "@/components/document-manager";
import { ChevronDown, Plus, Loader2, AlertCircle } from "lucide-react";
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
import { useAuthContext } from "@/providers/Auth";

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
  const { session } = useAuthContext();
  const [collections, setCollections] = useState<Collection[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [documentManagerOpen, setDocumentManagerOpen] = useState(false);

  // Memoize loadCollections with useCallback to avoid useEffect dependency issues
  const loadCollections = useCallback(async () => {
    const accessToken = session?.accessToken;
    if (!accessToken) {
      setError("Not authenticated");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const response = await documentApiClient.listCollections({
        accessToken,
      });
      setCollections(response.collections);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to load collections";
      setError(errorMessage);
      toast.error("Failed to load collections", {
        description: errorMessage,
      });
    } finally {
      setLoading(false);
    }
  }, [session?.accessToken]);

  // Load collections on mount and when userId changes
  useEffect(() => {
    loadCollections();
  }, [loadCollections]);

  const toggleCollection = useCallback(
    (collectionId: string) => {
      const isSelected = selectedCollectionIds.includes(collectionId);
      if (isSelected) {
        onSelectionChange(
          selectedCollectionIds.filter((id) => id !== collectionId),
        );
      } else {
        onSelectionChange([...selectedCollectionIds, collectionId]);
      }
    },
    [selectedCollectionIds, onSelectionChange],
  );

  const handleCreateNew = useCallback(() => {
    setDocumentManagerOpen(true);
  }, []);

  const handleDocumentManagerClose = useCallback(() => {
    setDocumentManagerOpen(false);
    // Refresh collections after closing document manager
    loadCollections();
  }, [loadCollections]);

  // Memoize computed values
  const selectedCount = useMemo(
    () => selectedCollectionIds.length,
    [selectedCollectionIds],
  );

  const selectedNames = useMemo(
    () =>
      collections
        .filter((c) => selectedCollectionIds.includes(c.id))
        .map((c) => c.name),
    [collections, selectedCollectionIds],
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
        className="flex h-10 items-center gap-2 rounded-lg border border-gray-300 bg-white px-4"
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
          className="flex h-10 items-center gap-2 rounded-lg border-red-300 bg-red-50 px-4 text-red-700 hover:bg-red-100"
          onClick={loadCollections}
        >
          <AlertCircle className="h-4 w-4" />
          <span className="hidden font-medium sm:inline">Failed to load</span>
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
          className="flex h-10 items-center gap-2 rounded-lg border border-gray-300 bg-white px-3 transition-colors hover:bg-gray-50 sm:px-4"
          onClick={handleCreateNew}
        >
          <Plus className="h-4 w-4 flex-shrink-0" />
          <span className="text-sm font-medium whitespace-nowrap sm:text-base">
            Create Your Knowledge Base
          </span>
        </Button>

        <Sheet
          open={documentManagerOpen}
          onOpenChange={setDocumentManagerOpen}
        >
          <SheetContent
            side="right"
            className="w-full p-0 sm:max-w-4xl"
          >
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
              "flex h-10 items-center gap-2 rounded-lg border border-gray-300 bg-white px-3 transition-colors hover:bg-gray-50 sm:px-4",
              selectedCount > 0 && "border-primary bg-primary/5",
            )}
          >
            <span className="max-w-[120px] truncate text-sm font-medium sm:max-w-[200px] sm:text-base">
              {buttonText}
            </span>
            <ChevronDown className="h-4 w-4 flex-shrink-0 opacity-50" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent
          align="start"
          className="max-h-[500px] w-80 overflow-y-auto bg-white dark:bg-gray-900"
          onCloseAutoFocus={(e) => {
            // Prevent auto-focus after closing to improve multi-select UX
            e.preventDefault();
          }}
        >
          <DropdownMenuLabel className="flex items-center justify-between">
            <span>
              Select Collections
              {selectedCount > 0 && (
                <span className="text-muted-foreground ml-2 text-xs font-normal">
                  ({selectedCount} of {collections.length})
                </span>
              )}
            </span>
          </DropdownMenuLabel>

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
                checkPosition="right"
                className="cursor-pointer"
              >
                <div className="flex min-w-0 flex-1 flex-col gap-0.5 py-1">
                  <span className="truncate font-medium">
                    {collection.name}
                  </span>
                  <div className="text-muted-foreground flex items-center gap-2 text-xs">
                    <span>
                      {collection.document_count} document
                      {collection.document_count !== 1 ? "s" : ""}
                    </span>
                    {collection.description && (
                      <>
                        <span>•</span>
                        <span
                          className="truncate"
                          title={collection.description}
                        >
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
              className="h-9 w-full justify-start"
              onClick={(e) => {
                e.stopPropagation();
                handleCreateNew();
              }}
            >
              <Plus className="mr-2 h-4 w-4" />
              Create New Collection
            </Button>
          </div>

          {/* Footer Info */}
          {selectedCount > 0 && (
            <>
              <DropdownMenuSeparator />
              <div className="text-muted-foreground px-2 py-2 text-xs">
                {selectedCount === collections.length
                  ? "Searching all collections"
                  : `Searching ${selectedCount} collection${selectedCount !== 1 ? "s" : ""}`}
              </div>
            </>
          )}
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Document Manager Sheet */}
      <Sheet
        open={documentManagerOpen}
        onOpenChange={setDocumentManagerOpen}
      >
        <SheetContent
          side="right"
          className="w-full p-0 sm:max-w-4xl"
        >
          <DocumentManager
            userId={userId}
            onClose={handleDocumentManagerClose}
          />
        </SheetContent>
      </Sheet>
    </>
  );
}
