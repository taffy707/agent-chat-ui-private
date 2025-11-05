# LangGraph Collection Filtering Implementation Guide

## Overview

This document describes the changes made to the LangGraph retrieval agent to support filtering search results by collection IDs. This allows users to select specific document collections to search, rather than searching all collections.

## Problem Statement

The original LangGraph retrieval agent would search across all documents for a user without the ability to filter by specific collections. We needed to add the ability to:

1. Accept a list of collection IDs from the frontend
2. Filter Vertex AI Search results to only return documents from selected collections
3. Maintain backward compatibility (if no collections specified, search all)

## Architecture Context

### Frontend to Backend Flow

```
User selects collections in UI
    ↓
Frontend sends collection_ids in message context
    ↓
LangGraph receives collection_ids in configuration
    ↓
Vertex AI Search applies metadata filters
    ↓
Returns only documents from selected collections
```

### Key Files Modified in LangGraph

1. **`src/retrieval_graph/configuration.py`** - Configuration schema
2. **`src/retrieval_graph/retrieval.py`** - Retrieval logic with filtering

---

## Detailed Implementation

### 1. Configuration Changes (`configuration.py`)

**File**: `src/retrieval_graph/configuration.py`

**What to add**: A new field to the configuration class to accept collection IDs from the frontend.

```python
from dataclasses import field

# Add this field to your IndexConfiguration class (or equivalent configuration class)
collection_ids: list[str] = field(
    default_factory=list,
    metadata={
        "description": "List of collection IDs to filter search results. If empty, searches all collections for the user."
    }
)
```

**Context**:

- This field receives the collection IDs passed from the frontend via the message context
- It defaults to an empty list `[]` for backward compatibility
- The frontend sends this as: `{"user_id": "default-user", "collection_ids": ["id1", "id2"]}`

---

### 2. Retrieval Logic Changes (`retrieval.py`)

**File**: `src/retrieval_graph/retrieval.py`

**Location**: Inside the function that creates/configures the Vertex AI retriever (likely named `make_vertex_ai_retriever` or similar)

**What to modify**: The Vertex AI Search retriever configuration to include metadata filters.

#### Original Code (Approximate)

```python
def make_vertex_ai_retriever(configuration: IndexConfiguration):
    # ... other code ...

    search_kwargs = {
        # existing parameters
    }

    # Only user_id filter (or no filter at all)
    if configuration.user_id:
        search_kwargs["filter"] = f'user_id: ANY("{configuration.user_id}")'

    retriever = VertexAISearchRetriever(
        # ... other parameters ...
        **search_kwargs
    )

    return retriever
```

#### Updated Code with Collection Filtering

```python
def make_vertex_ai_retriever(configuration: IndexConfiguration):
    # ... other code ...

    search_kwargs = {
        # existing parameters like max_documents, etc.
    }

    # Build filter expression dynamically
    filter_parts = []

    # Add user_id filter (if not disabled by your implementation)
    # Note: Check if you have a disable_user_filter flag or similar
    if configuration.user_id:  # or: if not disable_user_filter
        user_filter = f'user_id: ANY("{configuration.user_id}")'
        filter_parts.append(user_filter)

    # Add collection_ids filter if collections are specified
    if configuration.collection_ids:
        # Build collection filter for each collection ID
        collection_filters = [
            f'collection_id: ANY("{cid}")'
            for cid in configuration.collection_ids
        ]

        if len(collection_filters) == 1:
            # Single collection: collection_id: ANY("id1")
            filter_parts.append(collection_filters[0])
        else:
            # Multiple collections: (collection_id: ANY("id1") OR collection_id: ANY("id2"))
            combined_collection_filter = " OR ".join(collection_filters)
            filter_parts.append(f"({combined_collection_filter})")

    # Combine all filter parts with AND
    if filter_parts:
        filter_expr = " AND ".join(filter_parts)
        search_kwargs["filter"] = filter_expr

    retriever = VertexAISearchRetriever(
        # ... other parameters ...
        **search_kwargs
    )

    return retriever
```

---

## Filter Expression Examples

Understanding the filter syntax is crucial. Here are examples of what the final filter looks like:

### Example 1: User filter only (no collections selected)

```
user_id: ANY("default-user")
```

**Behavior**: Returns all documents for this user across all collections

### Example 2: User filter + Single collection

```
user_id: ANY("default-user") AND collection_id: ANY("collection-123")
```

**Behavior**: Returns documents only from collection-123 for this user

### Example 3: User filter + Multiple collections

```
user_id: ANY("default-user") AND (collection_id: ANY("collection-123") OR collection_id: ANY("collection-456"))
```

**Behavior**: Returns documents from collection-123 OR collection-456 for this user

### Example 4: Collections only (if user filter disabled)

```
(collection_id: ANY("collection-123") OR collection_id: ANY("collection-456"))
```

---

## Frontend Context (Already Implemented)

The frontend sends the following context with each message:

```typescript
// From: src/components/thread/index.tsx
const context = {
  ...artifactContext,
  user_id: "default-user",
  collection_ids: selectedCollectionIds, // Array of collection IDs
};

stream.sendMessage({
  messages: [...toolMessages, newHumanMessage],
  config: { configurable: context },
});
```

**Important**: The `collection_ids` is an array that can be:

- Empty `[]` - means search ALL collections
- Single item `["id1"]` - search only one collection
- Multiple items `["id1", "id2", "id3"]` - search specific collections

---

## Testing the Implementation

### Test Case 1: No Collections Selected

**Frontend sends**: `collection_ids: []`
**Expected filter**: `user_id: ANY("default-user")`
**Expected behavior**: Search all collections

### Test Case 2: One Collection Selected

**Frontend sends**: `collection_ids: ["abc-123"]`
**Expected filter**: `user_id: ANY("default-user") AND collection_id: ANY("abc-123")`
**Expected behavior**: Search only collection abc-123

### Test Case 3: Multiple Collections Selected

**Frontend sends**: `collection_ids: ["abc-123", "def-456"]`
**Expected filter**:

```
user_id: ANY("default-user") AND (collection_id: ANY("abc-123") OR collection_id: ANY("def-456"))
```

**Expected behavior**: Search collections abc-123 and def-456

---

## Vertex AI Search Metadata Requirements

**CRITICAL**: For this filtering to work, your documents in Vertex AI Search MUST have the following metadata fields:

1. **`user_id`** (string) - The user who owns the document
2. **`collection_id`** (string) - The collection the document belongs to

These fields must be indexed as **filterable** in your Vertex AI Search data schema.

### Example Document Metadata

```json
{
  "id": "doc-123",
  "content": "Document content here...",
  "user_id": "default-user",
  "collection_id": "research-papers"
  // ... other metadata
}
```

---

## Common Issues & Debugging

### Issue 1: Filter Not Working

**Symptom**: All documents returned regardless of collection selection
**Check**:

1. Verify `collection_ids` is being passed in configuration
2. Add logging: `print(f"Filter expression: {filter_expr}")`
3. Verify metadata fields exist in Vertex AI Search
4. Check field names match exactly (`collection_id` vs `collectionId`)

### Issue 2: No Results When Collections Selected

**Symptom**: No results when collections are selected, but works without selection
**Check**:

1. Verify documents have `collection_id` metadata
2. Verify the collection IDs match exactly (case-sensitive)
3. Check Vertex AI Search schema has `collection_id` as filterable field

### Issue 3: Syntax Errors in Filter

**Symptom**: Vertex AI Search returns error about filter syntax
**Check**:

1. Verify filter follows Vertex AI Search syntax: `field: ANY("value")`
2. Ensure OR conditions are wrapped in parentheses
3. Check for proper quote escaping

---

## Additional Notes

### Backward Compatibility

The implementation maintains backward compatibility:

- If `collection_ids` field doesn't exist in config → searches all collections
- If `collection_ids` is empty array → searches all collections
- Existing code without collection filtering continues to work

### Performance Considerations

- Filtering at the Vertex AI Search level is more efficient than filtering results in code
- Using metadata filters reduces the number of documents returned
- Multiple collection filters use OR logic (union of results)

### Security Considerations

- Always include `user_id` filter to prevent cross-user data access
- Validate collection IDs belong to the requesting user (if implementing server-side)
- Consider rate limiting collection selection (e.g., max 10 collections)

---

## Rebuilding the LangGraph Container

After making these changes, you must rebuild the LangGraph Docker container:

```bash
# Navigate to your LangGraph directory
cd /path/to/retrieval-agent-template

# Rebuild the Docker image
docker build -t retrieval-agent .

# Or if using LangGraph CLI
langgraph build

# Restart the container
docker-compose down
docker-compose up -d
```

---

## Summary of Changes

1. **Added `collection_ids` field** to configuration schema
2. **Modified retriever creation** to build dynamic filter expressions
3. **Implemented filter logic** that:
   - Combines user_id and collection_ids with AND
   - Combines multiple collection_ids with OR
   - Wraps multiple collections in parentheses
   - Handles empty collection list (searches all)
4. **Maintained backward compatibility** with existing code

---

## Questions to Verify Implementation

When re-implementing, confirm:

1. ✅ Does your configuration class accept `collection_ids: list[str]`?
2. ✅ Does your Vertex AI retriever support `filter` parameter in search_kwargs?
3. ✅ Are your documents in Vertex AI Search indexed with `collection_id` metadata?
4. ✅ Is `collection_id` marked as filterable in the Vertex AI Search schema?
5. ✅ Have you rebuilt and restarted the LangGraph container after changes?

---

## Example Implementation Checklist

- [ ] Add `collection_ids` field to configuration class
- [ ] Locate the Vertex AI retriever creation function
- [ ] Add filter building logic (user_id + collection_ids)
- [ ] Handle empty collection_ids case (search all)
- [ ] Handle single vs multiple collections (parentheses logic)
- [ ] Test with no collections selected
- [ ] Test with one collection selected
- [ ] Test with multiple collections selected
- [ ] Verify metadata exists in Vertex AI Search
- [ ] Rebuild Docker container
- [ ] Restart LangGraph server
- [ ] Test end-to-end from frontend

---

**End of Implementation Guide**
