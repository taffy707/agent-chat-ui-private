# Vertex AI Deletion Investigation

## Issue Report
**Date**: November 3, 2025
**Reported by**: User
**Issue**: Documents deleted from UI can still be found by retrieval agent

## Current Understanding

### What We Know ✅

1. **GCS Deletion Works**: Files are immediately deleted from Google Cloud Storage
2. **PostgreSQL Deletion Works**: Metadata is immediately removed from database
3. **Deletion Queue Exists**: Background worker retries Vertex AI deletions

### What's Happening ⚠️

When you delete a document, three things need to happen:
```
1. Delete from GCS        → ✅ INSTANT (works)
2. Delete from PostgreSQL → ✅ INSTANT (works)
3. Delete from Vertex AI  → ⚠️ ASYNC (problematic)
```

### The Vertex AI Indexing Pipeline

```
Upload File
    ↓
GCS Storage (instant)
    ↓
Trigger Vertex AI Import (instant)
    ↓
Vertex AI Processing Queue (1-30 minutes!)
    ↓
    - Chunking
    - Embedding
    - Indexing
    ↓
Document Searchable
```

### The Problem Scenario

**Timeline**:
1. **T+0**: User uploads document → Goes to GCS + triggers import
2. **T+1**: User deletes document → Removed from GCS + PostgreSQL
3. **T+1**: System tries to delete from Vertex AI → **404 ERROR** (not indexed yet!)
4. **T+1 to T+10 hours**: Deletion queue retries 10 times → All fail with 404
5. **T+15 minutes**: Vertex AI finishes indexing the DELETED document
6. **RESULT**: Document is gone from GCS/PostgreSQL but **STILL SEARCHABLE** in Vertex AI!

## Evidence from Your System

### Deletion Queue Status
```
pending: 4 documents (still retrying)
failed:  6 documents (gave up after 10 attempts)
total:   10 documents stuck
```

### Failed Deletions
These documents reached max retries and gave up:
```sql
vertex_ai_doc_id                               | status
------------------------------------------------+--------
62b9971d6d37_1-s2.0-S1470160X21011821-main.pdf | failed
3c5749f7cc97_DeepSeek_OCR_paper.pdf            | failed
8ef5e9adcb44_1801.03528v1.pdf                  | failed
23f34702277f_070007_1_5.0184740.pdf            | failed
e4a6179a6fd2_179131.pdf                        | failed
c4dd9e426f3c_pasta_recipe.txt                  | failed
```

**These documents are likely STILL IN VERTEX AI SEARCH INDEX** 🔴

### What Happened
1. You uploaded these documents
2. You deleted them before Vertex AI finished indexing
3. Deletion queue tried 10 times to delete → All 404 (not found)
4. Queue gave up → Marked as "failed"
5. Later, Vertex AI finished processing and indexed the deleted documents
6. **Now they're searchable even though they should be deleted!**

## Testing the Issue

### Test 1: Search for Known Deleted Content

Pick one of the failed deletions above, for example "DeepSeek_OCR_paper.pdf":

1. Open your retrieval agent chat
2. Ask: "What do you know about DeepSeek OCR?"
3. **If you get results**: The document IS still in Vertex AI (BUG CONFIRMED)
4. **If you get nothing**: The document is properly deleted

### Test 2: Check Vertex AI Datastore Directly

You can use the Google Cloud Console to verify:

1. Go to: https://console.cloud.google.com/gen-app-builder/data-stores
2. Select your datastore: `metatask_1761751621392`
3. Look for documents tab
4. Search for document IDs from the failed list

## Root Cause Analysis

### The Core Problem

The deletion logic has a race condition:

```python
# Current flow (BROKEN)
1. Delete from GCS     ✅
2. Delete from DB      ✅
3. Try to delete from Vertex AI
   if document doesn't exist (404):
      → Retry 10 times
      → Give up
      → Mark as failed

# But what if...
4. Vertex AI finishes indexing AFTER we gave up?
   → Document becomes searchable
   → Never gets deleted
   → ORPHANED IN SEARCH INDEX! 🔴
```

### Why This Happens

**Vertex AI Import is a TWO-STEP process**:

**Step 1**: Trigger Import (returns immediately)
```python
operation = vertex_ai.import_documents(gcs_uris)
# Returns instantly with operation_id
```

**Step 2**: Async Processing (takes 1-30 minutes)
```
Vertex AI backend:
- Fetches files from GCS
- Processes content (OCR, chunking, embedding)
- Indexes document
- Makes searchable
```

**The gap between Step 1 and Step 2 is where deletions fail!**

## Solutions

### Option 1: Wait for Indexing Before Allowing Deletion (BEST) ⭐

**Pros**:
- Guarantees no orphaned documents
- User sees clear "Processing..." state
- Deletions always succeed

**Cons**:
- User must wait 1-30 minutes before deleting new uploads
- More complex UI

**Implementation**:
1. Track import operation status
2. Poll Vertex AI for completion
3. Update document status: `uploaded` → `indexing` → `indexed`
4. Only allow deletion when status = `indexed`
5. Show "Processing..." badge in UI for indexing documents

### Option 2: Increase Retry Window (PARTIAL FIX) ⚙️

**Pros**:
- Simple fix
- Works for most cases

**Cons**:
- Still has race condition for very slow indexing
- Wastes resources on retries

**Implementation**:
```python
# Current: max_attempts = 10, retry every ~1 minute
# New: max_attempts = 60, retry every ~2 minutes
# Total window: 2 hours instead of 10 minutes
```

### Option 3: Manual Cleanup Endpoint (WORKAROUND) 🔧

**Pros**:
- Fixes existing orphaned documents
- Good for admin/maintenance

**Cons**:
- Doesn't prevent future orphans
- Requires manual intervention

**Implementation**:
Add endpoint to force-delete specific Vertex AI documents by ID.

### Option 4: Purge API (NUCLEAR OPTION) ☢️

**Pros**:
- Can delete multiple documents at once
- Handles large-scale cleanup

**Cons**:
- Requires purge operation (24-48 hour process)
- Deletes ALL documents matching a filter
- Cannot target individual documents

## Recommended Fix

**IMPLEMENT OPTION 1** (Wait for Indexing):

### Phase 1: Track Index Status

Add to documents table:
```sql
ALTER TABLE documents
ADD COLUMN index_status VARCHAR(50) DEFAULT 'pending';

-- Values: pending, indexing, indexed, failed
```

### Phase 2: Poll Import Operations

```python
async def poll_import_operation(operation_name):
    """Check if import operation completed."""
    operation = vertex_ai.get_operation(operation_name)
    if operation.done:
        if operation.error:
            return "failed"
        return "indexed"
    return "indexing"
```

### Phase 3: Update UI

```typescript
// Document status badge
{document.index_status === 'indexing' && (
  <Badge variant="warning">
    <Loader2 className="animate-spin" />
    Processing...
  </Badge>
)}

// Disable delete button
<Button
  disabled={document.index_status !== 'indexed'}
  title={
    document.index_status === 'indexing'
      ? "Cannot delete while processing"
      : "Delete document"
  }
>
  Delete
</Button>
```

### Phase 4: Background Status Checker

```python
async def update_indexing_statuses():
    """Background task to check import operations."""
    pending_docs = await db.get_documents_by_status('indexing')
    for doc in pending_docs:
        status = await poll_import_operation(doc.import_operation_id)
        await db.update_document_status(doc.id, status)
```

## Immediate Action Items

### For You (User)

1. **Test if deleted documents are still searchable**:
   - Ask your retrieval agent about "DeepSeek OCR"
   - Ask about "pasta recipe"
   - See if it finds anything

2. **If documents ARE still searchable** (bug confirmed):
   - Need to manually clean up Vertex AI index
   - See "Manual Cleanup" section below

3. **Going forward**:
   - Wait 5-10 minutes after uploading before deleting
   - Or accept that some deletions might not work immediately

### For Developer (Fixing the Code)

1. **Short-term**: Increase retry attempts and window
   ```python
   # In deletion_queue.py
   max_attempts INT DEFAULT 60,  # Was: 10
   # Retry every 2 minutes instead of 1
   ```

2. **Long-term**: Implement indexing status tracking
   - Add `index_status` column
   - Track import operations
   - Poll for completion
   - Only allow deletion when indexed

## Manual Cleanup (For Existing Orphaned Documents)

### Step 1: Find Orphaned Documents

```sql
-- These failed to delete
SELECT vertex_ai_doc_id, original_filename
FROM deletion_queue
WHERE status = 'failed';
```

### Step 2: Try Manual Deletion

Use the document API or direct Vertex AI API:

```bash
# For each failed document
curl -X DELETE "https://discoveryengine.googleapis.com/v1/projects/169798107925/locations/global/collections/default_collection/dataStores/metatask_1761751621392/branches/0/documents/{vertex_ai_doc_id}"
```

### Step 3: Verify Deletion

Search for the content in your retrieval agent and confirm it's gone.

### Step 4: Clean Up Queue

```sql
-- Remove failed entries after manual cleanup
DELETE FROM deletion_queue WHERE status = 'failed';
```

## Prevention

To avoid this in the future:

1. ✅ **Don't delete immediately after uploading** - Wait 5-10 minutes
2. ⚙️ **Increase retry window** - Give more time for indexing to complete
3. ⭐ **Implement status tracking** - Only allow deletion when indexed
4. 📊 **Add monitoring** - Alert on failed deletions

## Questions to Answer

1. **Are the "failed" documents currently searchable?**
   - Test by asking retrieval agent about their content

2. **How long does Vertex AI indexing usually take?**
   - Check import operation timestamps
   - Measure time from upload to first successful search

3. **Do you need instant deletion?**
   - Or can users wait for "Processing" to complete?

4. **How often do users delete right after uploading?**
   - If rare, simple warning might be enough

---

**Next Steps**: Test if deleted documents are still searchable, then decide on fix approach.
