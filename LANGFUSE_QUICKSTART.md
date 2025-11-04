# Langfuse Integration - Quick Start Guide

## ✅ What Was Done

I've integrated Langfuse tracing into your Agent Chat UI! Every message your users send will now be automatically traced with full observability.

### Changes Made

1. **Added Session Management** - Tracks user sessions across page refreshes
2. **Added Langfuse Metadata** - Automatically passes user context to your Docker backend
3. **Updated Thread Component** - Both new messages and regenerated responses are traced

## 🚀 How to Test

### Step 1: Start Your Docker Backend

In your retrieval agent terminal:

```bash
cd /Users/tafadzwabwakura/retrieval-agent-template
docker-compose up -d
```

Verify Langfuse is enabled:

```bash
docker-compose logs langgraph-api | grep Langfuse
```

You should see:
```
✅ Langfuse client initialized successfully (Project: metatask)
🔍 Langfuse tracing enabled for RetrievalGraph
```

### Step 2: Start Your Frontend

In this terminal:

```bash
cd /Users/tafadzwabwakura/agent-chat-ui
npm run dev
# or
pnpm dev
```

### Step 3: Test the Integration

1. **Open your browser**: http://localhost:3000

2. **Send a test message**:
   - Select a knowledge base collection
   - Type: "What is photosynthesis?"
   - Click Send

3. **Check browser console** (F12):
   - You should see:
     ```
     🔍 Sending context to LangGraph: {
       user_id: "default-user",
       collection_ids: [...],
       collection_count: 1,
       session_id: "abc-123-..."
     }
     ```

4. **View in Langfuse**:
   - Open: https://cloud.langfuse.com/project/metatask
   - You should see a new trace appear!

## 📊 What You'll See in Langfuse

Click on any trace to see:

### Trace Details
- **User**: `default-user`
- **Session**: Unique session ID that persists across page refreshes
- **Tags**: `production`, `web-chat`, `agent-chat-ui`
- **Metadata**:
  - collection_ids
  - collection_count
  - timestamp
  - has_content_blocks

### Execution Flow
```
RetrievalGraph (total: ~3-5s)
├─ generate_query (~1s)
│  └─ LLM Call: groq/openai/gpt-oss-20b
│     • Tokens: 150 in / 20 out
│     • Cost: $0.0001
│
├─ retrieve (~0.5s)
│  └─ Vector Search
│     • Documents retrieved: 5
│     • Collections: your selected collections
│
└─ respond (~2s)
   └─ LLM Call: groq/openai/gpt-oss-120b
      • Tokens: 800 in / 200 out
      • Cost: $0.0015
```

## 🎯 What Gets Traced

### Every User Message
- ✅ Full conversation history
- ✅ User ID and session ID
- ✅ Selected knowledge base collections
- ✅ All LLM calls with token counts
- ✅ Document retrieval operations
- ✅ Query generation steps
- ✅ Response generation
- ✅ Total cost and latency

### Regenerated Messages
Same as above, plus:
- ✅ Tagged with `regenerate` tag
- ✅ Includes `action: regenerate` in metadata

## 🔍 Session Management

### How Sessions Work

**New Session Created When:**
- User opens the app for the first time
- User clears browser sessionStorage
- User closes and reopens the browser tab

**Session Persists Across:**
- Page refreshes
- Navigation within the app
- Browser back/forward

**Session ID Storage:**
- Stored in `sessionStorage.getItem('chat_session_id')`
- Automatically generated using UUID v4
- Check in browser DevTools → Application → Session Storage

### View All Sessions

In Langfuse dashboard:
1. Go to https://cloud.langfuse.com/project/metatask
2. Click "Sessions" in the left sidebar
3. See all user sessions grouped together
4. Click any session to see all traces in that conversation

## 🧪 Advanced Testing

### Test Multiple Messages in Same Session

1. Send message: "What is photosynthesis?"
2. Wait for response
3. Send follow-up: "How does it relate to cellular respiration?"
4. Check Langfuse - both should have the same `session_id`

### Test Regenerate

1. Send a message
2. Click "Regenerate" on the response
3. Check Langfuse - new trace should have `regenerate` tag

### Test Multiple Collections

1. Select multiple knowledge base collections
2. Send a message
3. Check Langfuse metadata - should show all collection IDs

### Test New Session

1. Open browser DevTools (F12)
2. Go to Application → Session Storage
3. Delete `chat_session_id`
4. Refresh the page
5. Send a new message
6. Check Langfuse - should have a new session_id

## 📈 Using Langfuse for Analytics

### Filter Traces

In Langfuse dashboard, filter by:
- **User**: `default-user` (or your actual user IDs)
- **Session**: Specific session ID
- **Tags**: `web-chat`, `regenerate`, etc.
- **Date Range**: Last 24h, 7d, 30d

### View Metrics

Check:
- **Latency**: How long queries take
- **Costs**: Token usage and costs per query
- **Quality**: Add user feedback (coming soon)
- **Errors**: Failed queries or timeouts

### Common Queries

**Most expensive queries:**
- Sort by "Cost" column in Langfuse

**Slowest queries:**
- Sort by "Latency" column

**Queries from specific collection:**
- Filter metadata by collection_ids

## 🐛 Troubleshooting

### No Traces Appearing

**Check Docker is running:**
```bash
docker ps | grep retrieval-agent
```

**Check Docker logs:**
```bash
docker-compose logs langgraph-api | tail -50
```

**Check frontend console:**
- Open browser DevTools (F12)
- Look for the debug log: `🔍 Sending context to LangGraph`

### Traces Missing Metadata

**Check browser console:**
```bash
# Should show session_id in the log
console.log(sessionStorage.getItem('chat_session_id'))
```

**Check network request:**
- Open DevTools → Network tab
- Look for POST request to `/threads/.../runs`
- Check Request Payload → config → metadata

### Session ID Not Persisting

**Clear and regenerate:**
```javascript
// In browser console
sessionStorage.removeItem('chat_session_id')
window.location.reload()
```

## 💡 Next Steps

### 1. Add Real User IDs

Update line 242 in `src/components/thread/index.tsx`:

```typescript
// Change from:
user_id: "default-user",

// To:
user_id: currentUser?.id || "anonymous",
```

Where `currentUser` comes from your auth system.

### 2. Add User Feedback

Implement thumbs up/down buttons to score traces:

```typescript
// Create /app/api/langfuse-score/route.ts
import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  const { trace_id, score, comment } = await req.json();

  // TODO: Call Langfuse API to score the trace
  // For now, just log it
  console.log('User feedback:', { trace_id, score, comment });

  return NextResponse.json({ success: true });
}
```

### 3. Monitor Production

Set up dashboards in Langfuse to monitor:
- Average latency per day
- Token costs per user
- Error rates
- Most common queries

### 4. Optimize Based on Data

Use Langfuse insights to:
- Identify slow queries → optimize retrieval
- Find expensive queries → adjust model selection
- Discover common questions → improve knowledge base
- Track user satisfaction → iterate on responses

## 📚 Resources

- **Your Langfuse Dashboard**: https://cloud.langfuse.com/project/metatask
- **Integration Guide**: [LANGFUSE_INTEGRATION.md](./LANGFUSE_INTEGRATION.md)
- **Langfuse Docs**: https://langfuse.com/docs
- **Backend Integration**: `/Users/tafadzwabwakura/retrieval-agent-template/LANGFUSE_SETUP.md`

---

**🎉 You're all set!** Every message sent through your chat UI is now automatically traced with full observability.

Start chatting and watch the traces appear in real-time at: https://cloud.langfuse.com/project/metatask
