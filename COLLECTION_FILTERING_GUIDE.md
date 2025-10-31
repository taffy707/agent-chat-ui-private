# Collection-Filtered Retrieval Guide

This guide explains how the collection filtering system works to enable users to search specific document collections when chatting with the agent.

## 🎯 Overview

Users can now select which knowledge base collections to search when asking questions. This filters the retrieval to only search documents in the selected collections, making responses more focused and relevant.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Frontend (Agent Chat UI)                     │
│                                                                   │
│  1. User selects collections via Knowledge Base Selector         │
│  2. UI shows: "Create Your Knowledge Base" (if none)            │
│     OR "Select Knowledge Base" dropdown (if collections exist)   │
│  3. Selected collection IDs stored in state                      │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                │ Message + Context
                                │ { user_id, collection_ids: [...] }
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                  LangGraph Server (Retrieval Agent)              │
│                                                                   │
│  1. Receives context with user_id and collection_ids            │
│  2. Builds Vertex AI Search filter:                             │
│     "user_id: ANY('alice') AND                                   │
│      (collection_id: ANY('id1') OR collection_id: ANY('id2'))"  │
│  3. Queries Vertex AI Search with filters                       │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                │ Filtered Query
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Google Vertex AI Search                        │
│                                                                   │
│  • Searches only documents matching:                             │
│    - user_id = "alice"                                          │
│    - collection_id IN ["id1", "id2"]                            │
│  • Returns filtered results                                      │
└─────────────────────────────────────────────────────────────────┘
```

## 📝 Implementation Details

### Frontend Changes

#### 1. **Knowledge Base Selector Component**
**File**: `src/components/thread/KnowledgeBaseSelector.tsx`

**Two States**:
```typescript
// No collections → Show "Create Your Knowledge Base" button
if (collections.length === 0) {
  return <CreateButton onClick={openDocumentManager} />
}

// Has collections → Show "Select Knowledge Base" dropdown
return <DropdownMenu with checkboxes />
```

**Features**:
- Multi-select with checkboxes
- Shows document count per collection
- "Create New Collection" option in dropdown
- Opens Document Manager for management

#### 2. **Thread Component Integration**
**File**: `src/components/thread/index.tsx`

**State Management**:
```typescript
const [selectedCollectionIds, setSelectedCollectionIds] = useState<string[]>([]);
```

**Context Passing**:
```typescript
const context = {
  ...artifactContext,
  user_id: "default-user",
  collection_ids: selectedCollectionIds,  // ← Passed to LangGraph
};

stream.submit({ messages, context }, options);
```

#### 3. **UI Dropdown Component**
**File**: `src/components/ui/dropdown-menu.tsx`

Built with Radix UI for accessible dropdown menus with checkboxes.

---

### Backend Changes (LangGraph Server)

#### 1. **Configuration Update**
**File**: `retrieval-agent-template/src/retrieval_graph/configuration.py`

Added `collection_ids` field:
```python
@dataclass(kw_only=True)
class IndexConfiguration:
    user_id: str = field(default="default-user")

    collection_ids: list[str] = field(
        default_factory=list,
        metadata={"description": "List of collection IDs to filter search"}
    )
    # ... other fields
```

#### 2. **Vertex AI Retriever Update**
**File**: `retrieval-agent-template/src/retrieval_graph/retrieval.py`

**Filter Building Logic**:
```python
def make_vertex_ai_retriever(configuration: IndexConfiguration):
    filter_parts = []

    # Add user_id filter
    if not disable_user_filter:
        user_filter = f'user_id: ANY("{configuration.user_id}")'
        filter_parts.append(user_filter)

    # Add collection_ids filter (NEW!)
    if configuration.collection_ids:
        collection_filters = [
            f'collection_id: ANY("{cid}")'
            for cid in configuration.collection_ids
        ]
        if len(collection_filters) == 1:
            filter_parts.append(collection_filters[0])
        else:
            # Multiple collections → OR them together
            combined = " OR ".join(collection_filters)
            filter_parts.append(f"({combined})")

    # Combine with AND
    filter_expr = " AND ".join(filter_parts)
    search_kwargs["filter"] = filter_expr

    # Query Vertex AI Search with filter
    retriever = VertexAISearchRetriever(filter=filter_expr, ...)
```

**Example Filter Output**:
```
user_id: ANY("default-user") AND (collection_id: ANY("abc123") OR collection_id: ANY("def456"))
```

---

## 🎨 UI/UX Flow

### Scenario 1: New User (No Collections)

```
┌──────────────────────────────────────┐
│ Type your message...                 │
│ ┌──────────────────────────────────┐ │
│ │ What is machine learning?        │ │
│ └──────────────────────────────────┘ │
│                                      │
│ [+ Create Your Knowledge Base]       │ ← Button appears
│                                      │
│ [ Hide Tool Calls ]  [Upload PDF]   │
│                            [Send]    │
└──────────────────────────────────────┘
```

**Click "Create Your Knowledge Base"** → Opens Document Manager

### Scenario 2: User With Collections

```
┌──────────────────────────────────────┐
│ Type your message...                 │
│ ┌──────────────────────────────────┐ │
│ │ What is machine learning?        │ │
│ └─────────────────────────────���────┘ │
│                                      │
│ [Select Knowledge Base ▼]            │ ← Dropdown appears
│  ┌────────────────────────────────┐  │
│  │ ☑ Work Docs (12 docs)          │  │
│  │ ☑ Personal Notes (8 docs)      │  │
│  │ ☐ Archive (45 docs)            │  │
│  │ ─────────────────────────────  │  │
│  │ + Create New Collection        │  │
│  └────────────────────────────────┘  │
│                                      │
│ [ Hide Tool Calls ]  [Upload PDF]   │
│                            [Send]    │
└──────────────────────────────────────┘
```

**Collections Selected** → Button shows "2 Selected"

---

## 🔄 Data Flow Example

### Step-by-Step

1. **User selects collections**:
   - "Work Docs" (ID: `abc123`)
   - "Personal Notes" (ID: `def456`)

2. **User asks**: "What is our Q4 strategy?"

3. **Frontend sends to LangGraph**:
```json
{
  "messages": [
    {"type": "human", "content": "What is our Q4 strategy?"}
  ],
  "context": {
    "user_id": "default-user",
    "collection_ids": ["abc123", "def456"]
  }
}
```

4. **LangGraph processes**:
   - Reads `collection_ids` from context
   - Builds filter: `user_id: ANY("default-user") AND (collection_id: ANY("abc123") OR collection_id: ANY("def456"))`

5. **Vertex AI Search**:
   - Searches only documents where:
     - `user_id = "default-user"` AND
     - `collection_id = "abc123"` OR `collection_id = "def456"`
   - Returns only relevant docs from those 2 collections

6. **LangGraph responds**:
   - Uses filtered documents as context
   - Generates answer based only on Work Docs + Personal Notes
   - Archive collection (45 docs) completely ignored

---

## 🚀 How to Use

### For End Users

1. **Create Collections**:
   - Click "Create Your Knowledge Base"
   - Create a new collection (e.g., "Work Docs")
   - Upload documents to it

2. **Select Collections to Search**:
   - Click "Select Knowledge Base" dropdown
   - Check the collections you want to search
   - Selected collections highlighted with checkmark

3. **Ask Questions**:
   - Type your question
   - Agent searches ONLY selected collections
   - Get focused, relevant answers

4. **Change Selection Anytime**:
   - Uncheck collections to exclude them
   - Check more to expand search scope
   - No selection = searches all user collections

### For Developers

#### Debugging Collection Filters

**Check what's being sent**:
```typescript
console.log("Selected collections:", selectedCollectionIds);
console.log("Context:", context);
```

**Check LangGraph logs**:
```bash
cd retrieval-agent-template
docker-compose logs -f api | grep collection
```

**Check Vertex AI filter**:
```python
# In retrieval.py, add logging
print(f"Filter expression: {filter_expr}")
```

---

## 📊 Benefits

### User Benefits
✅ **Focused Results** - Search only relevant collections
✅ **Faster Answers** - Less noise from irrelevant docs
✅ **Organized Knowledge** - Separate work/personal/archive
✅ **Flexible Searching** - Mix & match collections

### Technical Benefits
✅ **Better Performance** - Smaller search space
✅ **Accurate Filtering** - Metadata-based, not fuzzy
✅ **Scalable** - Handles thousands of documents
✅ **Secure** - User-level isolation maintained

---

## 🔧 Configuration

### User ID

Currently hardcoded to `"default-user"`. To change:

**Frontend** (`src/components/thread/index.tsx`):
```typescript
<KnowledgeBaseSelector
  userId="alice"  // ← Change here
  selectedCollectionIds={selectedCollectionIds}
  onSelectionChange={setSelectedCollectionIds}
/>
```

**And in context**:
```typescript
const context = {
  user_id: "alice",  // ← Change here
  collection_ids: selectedCollectionIds,
};
```

### Default Behavior

**If no collections selected** (empty array):
- LangGraph searches ALL user's collections
- Only user_id filter applied
- No collection filter added

**To require selection**:
```typescript
// In handleSubmit, add validation:
if (selectedCollectionIds.length === 0) {
  toast.error("Please select at least one collection");
  return;
}
```

---

## 🧪 Testing

### Manual Test Flow

1. **Start both servers**:
```bash
# Terminal 1: Document API
cd document-api && ./docker-start.sh

# Terminal 2: LangGraph (already running)
# Check: docker ps | grep retrieval

# Terminal 3: Frontend
pnpm dev
```

2. **Create test collections**:
   - Open http://localhost:3000
   - Click "Create Your Knowledge Base"
   - Create "Test Collection 1"
   - Upload test document
   - Create "Test Collection 2"
   - Upload different document

3. **Test filtering**:
   - Select only "Test Collection 1"
   - Ask question related to doc in Collection 1
   - Verify response uses only that doc
   - Select only "Test Collection 2"
   - Ask same question
   - Verify response changes

### Expected Behavior

**Scenario A: Select Collection 1**
```
Q: "What does the document say?"
A: [Uses only documents from Collection 1]
```

**Scenario B: Select Collection 2**
```
Q: "What does the document say?"
A: [Uses only documents from Collection 2 - different answer]
```

**Scenario C: Select Both**
```
Q: "What does the document say?"
A: [Uses documents from both collections - combined answer]
```

---

## 📚 Related Files

### Frontend
- `src/components/thread/KnowledgeBaseSelector.tsx` - Selector component
- `src/components/thread/index.tsx` - Integration point
- `src/components/ui/dropdown-menu.tsx` - Dropdown UI
- `src/lib/document-api-client.ts` - Fetches collections
- `src/types/document-api.ts` - TypeScript types

### Backend (LangGraph)
- `retrieval-agent-template/src/retrieval_graph/configuration.py` - Config
- `retrieval-agent-template/src/retrieval_graph/retrieval.py` - Filter logic
- `retrieval-agent-template/src/retrieval_graph/graph.py` - Graph definition

### Document API
- `document-api/main.py` - Collections endpoints
- `document-api/database.py` - Collection metadata storage

---

## 🎯 Future Enhancements

Potential improvements:
- [ ] Save selected collections per user (persistence)
- [ ] Quick filters: "All", "Recent", "Favorites"
- [ ] Collection search/filter in dropdown
- [ ] Show collection descriptions in dropdown
- [ ] Collection color coding
- [ ] Keyboard shortcuts for selection
- [ ] "Search all" vs "Search selected" toggle
- [ ] Collection analytics (most used, etc.)

---

**Everything is ready to use!** Just select your collections and start chatting! 🚀
