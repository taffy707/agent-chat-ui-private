"use client";

import { Button } from "@/components/ui/button";
import { useThreads } from "@/providers/Thread";
import { Thread } from "@langchain/langgraph-sdk";
import { useEffect, useState } from "react";
import { getContentString } from "../utils";
import { useQueryState, parseAsBoolean, parseAsString } from "nuqs";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import {
  PanelRightOpen,
  PanelRightClose,
  SquarePen,
  FileText,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import { cn } from "@/lib/utils";
import { NavUser } from "./nav-user";

function ThreadList({
  threads,
  onThreadClick,
}: {
  threads: Thread[];
  onThreadClick?: (threadId: string) => void;
}) {
  const [threadId, setThreadId] = useQueryState("threadId");

  return (
    <div className="flex h-full w-full flex-col items-start justify-start gap-2 overflow-y-auto [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-gray-300 [&::-webkit-scrollbar-track]:bg-transparent">
      {threads.map((t) => {
        let itemText = t.thread_id;
        if (
          typeof t.values === "object" &&
          t.values &&
          "messages" in t.values &&
          Array.isArray(t.values.messages) &&
          t.values.messages?.length > 0
        ) {
          const firstMessage = t.values.messages[0];
          itemText = getContentString(firstMessage.content);
        }
        return (
          <div
            key={t.thread_id}
            className="w-full px-1"
          >
            <Button
              variant="ghost"
              className={cn(
                "hover:bg-sidebar-accent w-full items-start justify-start text-left font-normal",
                t.thread_id === threadId && "bg-sidebar-accent",
              )}
              onClick={(e) => {
                e.preventDefault();
                onThreadClick?.(t.thread_id);
                if (t.thread_id === threadId) return;
                setThreadId(t.thread_id);
              }}
            >
              <p className="truncate text-ellipsis">{itemText}</p>
            </Button>
          </div>
        );
      })}
    </div>
  );
}

function ThreadHistoryLoading() {
  return (
    <div className="flex h-full w-full flex-col items-start justify-start gap-2 overflow-y-auto [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-gray-300 [&::-webkit-scrollbar-track]:bg-transparent">
      {Array.from({ length: 10 }).map((_, i) => (
        <Skeleton
          key={`skeleton-${i}`}
          className="h-10 w-full"
        />
      ))}
    </div>
  );
}

export default function Sidebar() {
  const isLargeScreen = useMediaQuery("(min-width: 1024px)");
  const [chatHistoryOpen, setChatHistoryOpen] = useQueryState(
    "chatHistoryOpen",
    parseAsBoolean.withDefault(false),
  );
  const [view, setView] = useQueryState(
    "view",
    parseAsString.withDefault("chat"),
  );
  const [, setThreadId] = useQueryState("threadId");
  const [historyExpanded, setHistoryExpanded] = useState(false);

  const { getThreads, threads, setThreads, threadsLoading, setThreadsLoading } =
    useThreads();

  useEffect(() => {
    if (typeof window === "undefined") return;
    setThreadsLoading(true);
    getThreads()
      .then(setThreads)
      .catch(console.error)
      .finally(() => setThreadsLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleNewThread = () => {
    setThreadId(null);
    setView("chat");
  };

  const handleManageDocuments = () => {
    setView("documents");
  };

  // Desktop sidebar content
  const sidebarContent = (
    <div className="bg-sidebar flex h-full flex-col">
      {/* Sidebar Header with collapse button */}
      <div className="border-sidebar-border flex items-center justify-between border-b p-4">
        <h2 className="text-sidebar-foreground text-lg font-semibold">
          Navigation
        </h2>
        <Button
          variant="ghost"
          size="icon"
          className="hover:bg-sidebar-accent"
          onClick={() => setChatHistoryOpen((p) => !p)}
        >
          {chatHistoryOpen ? (
            <PanelRightClose className="size-5" />
          ) : (
            <PanelRightOpen className="size-5" />
          )}
        </Button>
      </div>

      {/* Navigation Items */}
      <div className="flex flex-col gap-1 p-2">
        {/* New Thread Button */}
        <Button
          variant="ghost"
          className="hover:bg-sidebar-accent w-full justify-start gap-3"
          onClick={handleNewThread}
        >
          <SquarePen className="size-5" />
          <span>New Thread</span>
        </Button>

        {/* Manage Documents Button */}
        <Button
          variant="ghost"
          className={cn(
            "hover:bg-sidebar-accent w-full justify-start gap-3",
            view === "documents" && "bg-sidebar-accent",
          )}
          onClick={handleManageDocuments}
        >
          <FileText className="size-5" />
          <span>Manage Documents</span>
        </Button>
      </div>

      {/* Thread History Section */}
      <div className="border-sidebar-border flex flex-1 flex-col overflow-hidden border-t">
        <Button
          variant="ghost"
          className="hover:bg-sidebar-accent w-full justify-start gap-2 rounded-none p-4"
          onClick={() => setHistoryExpanded(!historyExpanded)}
        >
          {historyExpanded ? (
            <ChevronDown className="size-4" />
          ) : (
            <ChevronRight className="size-4" />
          )}
          <span className="font-semibold">Thread History</span>
          <span className="text-muted-foreground ml-auto text-xs">
            ({threads.length})
          </span>
        </Button>

        {/* Thread List - Only visible when expanded */}
        {historyExpanded && (
          <div className="flex-1 overflow-hidden p-2">
            {threadsLoading ? (
              <ThreadHistoryLoading />
            ) : (
              <ThreadList threads={threads} />
            )}
          </div>
        )}
      </div>

      {/* User Profile Section at Bottom */}
      <NavUser />
    </div>
  );

  return (
    <>
      {/* Desktop Sidebar */}
      <div className="hidden lg:flex">{sidebarContent}</div>

      {/* Mobile Sheet */}
      <div className="lg:hidden">
        <Sheet
          open={!!chatHistoryOpen && !isLargeScreen}
          onOpenChange={(open) => {
            if (isLargeScreen) return;
            setChatHistoryOpen(open);
          }}
        >
          <SheetContent
            side="left"
            className="w-[300px] p-0"
          >
            <SheetHeader className="sr-only">
              <SheetTitle>Navigation Menu</SheetTitle>
            </SheetHeader>
            {sidebarContent}
          </SheetContent>
        </Sheet>
      </div>
    </>
  );
}
