# Langfuse Integration for Agent Chat UI

This guide shows you how to add Langfuse tracing to your existing Agent Chat UI that connects to your Dockerized LangGraph agent.

## What This Does

When users send messages through your chat UI:
1. **Frontend** sends message with Langfuse metadata
2. **Docker LangGraph API** (localhost:8123) processes it
3. **Langfuse** automatically captures everything:
   - Full conversation trace
   - All LLM calls with token counts
   - Document retrieval operations
   - Query generation steps
   - User context and sessions

## Step 1: Update Environment Variables

Add to your `.env` file:

```bash
# Existing configuration
NEXT_PUBLIC_API_URL=http://localhost:8123
NEXT_PUBLIC_ASSISTANT_ID=retrieval_graph
NEXT_PUBLIC_DOCUMENT_API_URL=http://localhost:8000

# Add these for Langfuse tracing
NEXT_PUBLIC_LANGFUSE_ENABLED=true
```

That's it! Your Docker deployment already has the Langfuse credentials configured.

## Step 2: Update Thread Component

Open `/src/components/thread/index.tsx` and find where `stream.submit()` is called (around line 240).

### Current Code:
```typescript
stream.submit(
  { messages: [...toolMessages, newHumanMessage] },
  {
    config: { configurable: context },
    streamMode: ["values"],
    streamSubgraphs: true,
    streamResumable: true,
    optimisticValues: (prev) => ({
      ...prev,
      messages: [
        ...(prev.messages ?? []),
        ...toolMessages,
        newHumanMessage,
      ],
    }),
  },
);
```

### Updated Code with Langfuse:
```typescript
// Add session ID management at the top of the Thread component
const [sessionId] = useState(() => {
  if (typeof window !== 'undefined' && window.sessionStorage) {
    let sid = sessionStorage.getItem('chat_session_id');
    if (!sid) {
      sid = uuidv4();
      sessionStorage.setItem('chat_session_id', sid);
    }
    return sid;
  }
  return uuidv4();
});

// Then update the stream.submit call:
stream.submit(
  { messages: [...toolMessages, newHumanMessage] },
  {
    config: {
      configurable: context,
      // Add Langfuse metadata here 👇
      metadata: {
        langfuse_user_id: context.user_id || 'anonymous',
        langfuse_session_id: sessionId,
        langfuse_tags: ['production', 'web-chat'],
        // Additional context
        collection_ids: context.collection_ids,
        collection_count: context.collection_ids?.length || 0,
        timestamp: new Date().toISOString(),
      }
    },
    streamMode: ["values"],
    streamSubgraphs: true,
    streamResumable: true,
    optimisticValues: (prev) => ({
      ...prev,
      messages: [
        ...(prev.messages ?? []),
        ...toolMessages,
        newHumanMessage,
      ],
    }),
  },
);
```

## Step 3: Complete Integration Code

Here's the complete updated code for your Thread component:

```typescript
// At the top of the Thread component (after line 150), add:
const [sessionId] = useState(() => {
  if (typeof window !== 'undefined' && window.sessionStorage) {
    let sid = sessionStorage.getItem('chat_session_id');
    if (!sid) {
      sid = uuidv4();
      sessionStorage.setItem('chat_session_id', sid);
    }
    return sid;
  }
  return uuidv4();
});

// Then find the handleSubmit function and update the stream.submit call:
const handleSubmit = async (e: FormEvent) => {
  e.preventDefault();

  if (!input.trim() || isLoading) {
    return;
  }

  const toolMessages = ensureToolCallsHaveResponses(stream.messages);

  const newHumanMessage = {
    type: "human" as const,
    id: uuidv4(),
    content: contentBlocks.length > 0 ? [input, ...contentBlocks] : input,
  };

  resetBlocks();
  setInput("");

  const context = {
    user_id: selectedUserId || "default_user",
    collection_ids: selectedCollectionIds.length > 0 ? selectedCollectionIds : undefined,
    collection_count: selectedCollectionIds.length,
  };

  console.log("🚀 Submitting with context:", {
    user_id: context.user_id,
    collection_ids: context.collection_ids,
    collection_count: context.collection_count,
  });

  stream.submit(
    { messages: [...toolMessages, newHumanMessage] },
    {
      config: {
        configurable: context,
        // ✨ Langfuse metadata - automatically traced!
        metadata: {
          langfuse_user_id: context.user_id || 'anonymous',
          langfuse_session_id: sessionId,
          langfuse_tags: ['production', 'web-chat', 'agent-chat-ui'],
          // Additional debug info
          collection_ids: context.collection_ids,
          collection_count: context.collection_count,
          has_content_blocks: contentBlocks.length > 0,
          timestamp: new Date().toISOString(),
          frontend_version: '1.0.0',
        }
      },
      streamMode: ["values"],
      streamSubgraphs: true,
      streamResumable: true,
      optimisticValues: (prev) => ({
        ...prev,
        messages: [
          ...(prev.messages ?? []),
          ...toolMessages,
          newHumanMessage,
        ],
      }),
    },
  );

  prevMessageLength.current = prevMessageLength.current + toolMessages.length + 1;
};
```

## Step 4: Test the Integration

### 1. Start Your Docker Services

In your retrieval agent directory:

```bash
cd /Users/tafadzwabwakura/retrieval-agent-template
docker-compose up -d
```

Verify Langfuse is enabled:
```bash
docker-compose logs langgraph-api | grep Langfuse
```

Should show:
```
✅ Langfuse client initialized successfully (Project: metatask)
🔍 Langfuse tracing enabled for RetrievalGraph
```

### 2. Start Your Frontend

In your frontend directory:

```bash
cd /Users/tafadzwabwakura/agent-chat-ui
npm run dev
# or
pnpm dev
```

### 3. Send a Test Message

1. Open http://localhost:3000
2. Select a knowledge base collection
3. Send a message: "What is photosynthesis?"
4. Watch your browser console - you should see the context being logged

### 4. View in Langfuse

Open: https://cloud.langfuse.com/project/metatask

You should see a new trace with:
- **Trace Name**: "RetrievalGraph"
- **User ID**: Your user_id (or "anonymous")
- **Session ID**: The session ID from sessionStorage
- **Tags**: ["production", "web-chat", "agent-chat-ui"]
- **Metadata**: collection_ids, timestamp, etc.
- **Full execution**: generate_query → retrieve → respond
- **All LLM calls**: with tokens and costs

## What You'll See in Langfuse

For each chat message, Langfuse captures:

### Trace Overview
- User who sent the message
- Session grouping multiple messages
- Total latency and cost
- Tags for filtering

### Execution Details
- **generate_query node**: How the search query was generated
- **retrieve node**: Documents retrieved from your collections
- **respond node**: Final response generation
- **LLM calls**: Token counts, model used, parameters
- **Context**: All the metadata you passed

### Example Trace Structure
```
RetrievalGraph
├─ generate_query
│  └─ LLM Call (groq/openai/gpt-oss-20b)
│     • Input: conversation history
│     • Output: search query
│     • Tokens: 150 input, 20 output
├─ retrieve
│  └─ Vector Search
│     • Query: generated search query
│     • Results: 5 documents
│     • Collections: [your selected collections]
└─ respond
   └─ LLM Call (groq/openai/gpt-oss-120b)
      • Input: query + retrieved docs
      • Output: final response
      • Tokens: 800 input, 200 output
```

## Advanced: Add User Feedback

Want to capture thumbs up/down feedback? Add this to your message component:

```typescript
import { useState } from 'react';

function MessageFeedback({ messageId }: { messageId: string }) {
  const [feedback, setFeedback] = useState<'positive' | 'negative' | null>(null);

  const handleFeedback = async (value: 'positive' | 'negative') => {
    setFeedback(value);

    // Send to your backend API route
    await fetch('/api/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message_id: messageId,
        feedback: value === 'positive' ? 1 : 0,
      }),
    });
  };

  return (
    <div className="flex gap-2 mt-2">
      <button
        onClick={() => handleFeedback('positive')}
        className={feedback === 'positive' ? 'text-green-500' : 'text-gray-400'}
      >
        👍
      </button>
      <button
        onClick={() => handleFeedback('negative')}
        className={feedback === 'negative' ? 'text-red-500' : 'text-gray-400'}
      >
        👎
      </button>
    </div>
  );
}
```

Then create `/app/api/feedback/route.ts`:

```typescript
import { NextResponse } from 'next/server';
// Note: Langfuse SDK would need to be installed on the backend
// For now, we can't score traces from the frontend directly

export async function POST(req: Request) {
  const { message_id, feedback } = await req.json();

  // TODO: Store feedback in your database
  // In production, you'd want to:
  // 1. Get the trace_id from your message tracking
  // 2. Use Langfuse Node SDK to score the trace
  // 3. Store feedback in your own database

  console.log('Feedback received:', { message_id, feedback });

  return NextResponse.json({ success: true });
}
```

## Session Management

The integration automatically manages sessions:

### New Session
When a user:
- Opens the app for the first time
- Clicks "New Chat" button
- Clears their sessionStorage

Add a "New Session" button:

```typescript
function NewSessionButton() {
  const handleNewSession = () => {
    // Clear session
    sessionStorage.removeItem('chat_session_id');
    // Refresh page to get new session
    window.location.reload();
  };

  return (
    <Button onClick={handleNewSession}>
      <Plus className="h-4 w-4" />
      New Session
    </Button>
  );
}
```

### Continuing Session
Users automatically continue their session across page refreshes until they close the browser tab.

## Debugging

### Check if metadata is being sent

Add this console log in your Thread component:

```typescript
console.log('📤 Sending to LangGraph with metadata:', {
  user_id: context.user_id,
  session_id: sessionId,
  collections: context.collection_ids,
});
```

### Check Docker logs

```bash
docker-compose logs -f langgraph-api
```

Look for trace activity.

### Check Langfuse

1. Open https://cloud.langfuse.com/project/metatask
2. Filter by:
   - **User**: Your user_id
   - **Session**: Your session_id
   - **Tags**: "web-chat"
3. Click on a trace to see details

### Common Issues

**Issue**: No traces appearing in Langfuse
- Check Docker logs: `docker-compose logs langgraph-api | grep Langfuse`
- Verify credentials in `.env.production`
- Check network: Can Docker reach cloud.langfuse.com?

**Issue**: Traces missing user context
- Verify metadata is in the config object
- Check that user_id is not null/undefined
- Look at browser console for logs

**Issue**: Session not persisting
- Check sessionStorage in browser DevTools
- Verify sessionStorage is not being cleared
- Check if user is in private/incognito mode

## Summary

You've integrated Langfuse! Now every chat message automatically:

✅ Traces the complete execution flow
✅ Captures all LLM calls with costs
✅ Groups by user and session
✅ Includes your custom metadata
✅ Shows document retrievals
✅ Available in real-time on Langfuse dashboard

**Next steps:**
1. Monitor your traces at https://cloud.langfuse.com/project/metatask
2. Add user feedback buttons (optional)
3. Create dashboards for common queries
4. Set up alerts for errors
5. Analyze token usage and costs

---

**Need Help?**
- Langfuse Docs: https://langfuse.com/docs
- LangChain Integration: https://langfuse.com/integrations/frameworks/langchain
- Your Dashboard: https://cloud.langfuse.com/project/metatask
