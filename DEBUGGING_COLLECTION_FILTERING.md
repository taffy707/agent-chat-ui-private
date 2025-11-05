# Debugging Collection Filtering

## Testing Steps

I've added console logging to help debug the collection filtering. Follow these steps:

### 1. Start the Frontend

```bash
pnpm dev
```

### 2. Open Browser Console

- Open your browser's Developer Tools (F12)
- Go to the Console tab
- Keep it open while testing

### 3. Test Scenario 1: No Collections Selected

1. **Don't select any collections** (leave dropdown empty)
2. Type a test question: "What documents do I have?"
3. Press Send
4. **Check console for**:
   ```
   📚 Selected collections changed: { count: 0, ids: [], isEmpty: true }
   🔍 Sending context to LangGraph: { user_id: 'default-user', collection_ids: [], collection_count: 0 }
   ```
5. **Expected behavior**: Should search ALL your collections

### 4. Test Scenario 2: One Collection Selected

1. Click the "Select Knowledge Base" dropdown
2. Select ONE collection (e.g., "research")
3. Type a test question about content you KNOW is in that collection
4. Press Send
5. **Check console for**:
   ```
   📚 Selected collections changed: { count: 1, ids: ['collection-id-here'], isEmpty: false }
   🔍 Sending context to LangGraph: { user_id: 'default-user', collection_ids: ['collection-id-here'], collection_count: 1 }
   ```
6. **Expected behavior**: Should ONLY return results from that collection

### 5. Test Scenario 3: Multiple Collections Selected

1. Select 2-3 collections from the dropdown
2. Ask a question
3. Press Send
4. **Check console for**:
   ```
   📚 Selected collections changed: { count: 3, ids: ['id1', 'id2', 'id3'], isEmpty: false }
   🔍 Sending context to LangGraph: { ... collection_ids: ['id1', 'id2', 'id3'], collection_count: 3 }
   ```
5. **Expected behavior**: Should return results from ANY of the selected collections

---

## What to Look For

### Frontend Issues

**Problem**: Console shows `collection_ids: []` even when collections are selected

- **Cause**: Selection not working in UI
- **Check**: Click the collection items - do they show checkmarks?

**Problem**: Console doesn't show any logs

- **Cause**: Frontend not running or console not open
- **Fix**: Restart frontend with `pnpm dev`

### Backend Issues

**Problem**: Frontend sends correct IDs but results aren't filtered

- **Cause**: LangGraph isn't applying the filter
- **Next step**: Check LangGraph logs

---

## Checking LangGraph Logs

### 1. Find your LangGraph container/process

```bash
# If using Docker
docker ps | grep langgraph
docker logs <container-id>

# If running directly
# Check the terminal where LangGraph is running
```

### 2. Look for filter-related logs

The LangGraph server should log the filter expression being used. Look for something like:

```
Filter: user_id: ANY("default-user") AND (collection_id: ANY("id1") OR collection_id: ANY("id2"))
```

### 3. If you DON'T see filter logs

The collection filtering code might not be implemented yet or was removed.

---

## Verifying the Filter is Working

### Create a Test Setup

1. **Create Collection A**: Upload a document about "Python programming"
2. **Create Collection B**: Upload a document about "JavaScript programming"

### Test 1: Search with Collection A selected only

- Ask: "Tell me about programming languages"
- **Expected**: Only mentions Python (from Collection A)
- **If it mentions JavaScript**: Filter is NOT working

### Test 2: Search with Collection B selected only

- Ask: "Tell me about programming languages"
- **Expected**: Only mentions JavaScript (from Collection B)
- **If it mentions Python**: Filter is NOT working

### Test 3: Search with both collections selected

- Ask: "Tell me about programming languages"
- **Expected**: Mentions both Python and JavaScript
- This should work either way

---

## Common Reasons Filtering Doesn't Work

### 1. LangGraph Code Not Implemented

**Check**: Is the collection filtering code in `retrieval.py`?

- If the other AI assistant reverted or didn't apply the changes
- Solution: Share the `LANGGRAPH_COLLECTION_FILTERING_CHANGES.md` guide

### 2. Environment Variable Conflict

**Check**: `VERTEX_AI_DISABLE_USER_FILTER=true`

- If filter code checks user_id but this is disabled, logic might break
- Solution: Update filter code to handle this flag correctly

### 3. Metadata Missing in Vertex AI Search

**Check**: Do your documents have `collection_id` metadata?

- If documents weren't indexed with collection_id, filter won't work
- Solution: Re-upload documents with proper metadata

### 4. Field Name Mismatch

**Check**: Frontend sends `collection_ids`, backend expects `collection_id`

- Or backend uses `collectionId` instead of `collection_id`
- Solution: Ensure field names match exactly

### 5. Filter Syntax Error

**Check**: Vertex AI Search filter syntax is correct

- Correct: `collection_id: ANY("abc-123")`
- Wrong: `collection_id == "abc-123"`
- Wrong: `collection_id: "abc-123"`

---

## Quick Diagnostic Checklist

Run through this checklist and note which ones PASS ✅ or FAIL ❌:

- [ ] Console shows collection IDs when I select collections
- [ ] Console shows correct count of selected collections
- [ ] Console logs appear when I send a message
- [ ] collection_ids array contains the correct IDs
- [ ] LangGraph server is running (not crashed)
- [ ] LangGraph receives the collection_ids (check backend logs)
- [ ] Documents in Vertex AI have `collection_id` metadata
- [ ] `VERTEX_AI_DISABLE_USER_FILTER` is set to `true` in LangGraph env
- [ ] Collection filtering code exists in `retrieval.py`
- [ ] Filter expression is being logged in LangGraph
- [ ] Test with known documents shows filtered results

---

## Next Steps Based on Results

### If Frontend Logs Look Good

✅ Console shows correct collection IDs
✅ IDs are sent on submit
❌ But results aren't filtered

→ **Problem is in LangGraph backend**
→ Check LangGraph logs
→ Verify collection filtering code is implemented
→ Share the implementation guide with the other AI

### If Frontend Logs Are Wrong

❌ Console shows empty array when collections selected
❌ No logs appear

→ **Problem is in frontend**
→ Check if KnowledgeBaseSelector is wired correctly
→ Verify state is being updated

### If Everything Looks Good But Still Not Working

✅ Frontend sends correct IDs
✅ LangGraph receives them
✅ Filter is being applied
❌ Results still seem wrong

→ **Problem might be with Vertex AI Search**
→ Check document metadata
→ Verify `collection_id` field exists and is indexed
→ Try querying Vertex AI directly with filters

---

## Share This Info

When asking the other AI to fix the LangGraph server, share:

1. **Console logs** showing what the frontend is sending
2. **LangGraph logs** showing what's being received
3. **The implementation guide**: `LANGGRAPH_COLLECTION_FILTERING_CHANGES.md`
4. **This info**: "VERTEX_AI_DISABLE_USER_FILTER=true is set, so don't include user_id in filter"
5. **Expected filter format**:
   - No collections: No filter (search all)
   - One collection: `collection_id: ANY("abc-123")`
   - Multiple: `(collection_id: ANY("abc-123") OR collection_id: ANY("def-456"))`

---

## Testing After Fix

Once the LangGraph code is updated:

1. **Rebuild LangGraph container**:

   ```bash
   cd /path/to/langgraph
   docker build -t retrieval-agent .
   docker-compose down
   docker-compose up -d
   ```

2. **Clear browser cache and refresh**

3. **Run through all test scenarios again**

4. **Verify console logs match expected behavior**

Good luck! 🚀
