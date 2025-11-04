# Vertex AI Search Deletion Verification Guide

## Yes, the Search Folder Shows Deletion Methods! ✅

The `/Users/tafadzwabwakura/Desktop/search` folder contains examples from Google's Vertex AI Search documentation that show **exactly** how to delete documents:

### 1. Individual Document Deletion (REST API)
**File**: `vais-building-blocks/inline_ingestion_of_documents.ipynb`

```python
def delete_document_datastore(
    project_id: str, location: str, data_store_id: str, document_id: str
) -> bool:
    """Deletes a specific document from a data store using the REST API."""

    base_url = (
        f"{location}-discoveryengine.googleapis.com"
        if location != "global"
        else "discoveryengine.googleapis.com"
    )
    url = f"https://{base_url}/v1alpha/projects/{project_id}/locations/{location}/collections/default_collection/dataStores/{data_store_id}/branches/default_branch/documents/{document_id}"

    response = authed_session.delete(url)
    response.raise_for_status()
    return True
```

**This is what your code uses!** ✅

### 2. Bulk Purge (Python SDK)
**File**: `tuning/vertexai-search-tuning.ipynb`

```python
def purge_documents(
    project_id: str,
    location: str,
    data_store_id: str,
) -> discoveryengine.PurgeDocumentsMetadata:
    client = discoveryengine.DocumentServiceClient()

    operation = client.purge_documents(
        request=discoveryengine.PurgeDocumentsRequest(
            parent=client.branch_path(...),
            filter="*",  # Delete all documents
            force=True,  # IMPORTANT: Must be True to actually delete!
        )
    )

    response = operation.result()
    return response
```

**Key Point**: The `force=True` parameter is critical - without it, the API just returns the count without actually deleting!

---

## How to Verify Deletion Actually Worked 🔍

I've added **three verification methods** to your code:

### Method 1: Automatic Verification (Built into Delete Endpoint)

When you delete a document, the API now **automatically verifies** the deletion and returns the status:

```bash
curl -X DELETE "http://localhost:8000/documents/{doc_id}?user_id={user_id}"
```

**Response includes verification**:
```json
{
  "status": "success",
  "message": "Document {id} deleted successfully",
  "deleted": {
    "document_id": "...",
    "original_filename": "bitcoin.pdf",
    "gcs_blob_name": "c0744c175a37_bitcoin.pdf",
    "vertex_ai_doc_id": "c0744c175a37_bitcoin.pdf"
  },
  "deletion_status": {
    "postgresql": true,
    "gcs": true,
    "vertex_ai": true
  },
  "vertex_ai_verification": {
    "verified": true,
    "message": "✅ Document successfully deleted from Vertex AI: c0744c175a37_bitcoin.pdf"
  }
}
```

If `vertex_ai_verification.verified` is `true`, the document is **confirmed deleted**!

### Method 2: Manual Verification Endpoint

Check if a specific document exists in Vertex AI:

```bash
curl "http://localhost:8000/debug/verify-document/c0744c175a37_bitcoin.pdf"
```

**If deleted successfully**:
```json
{
  "status": "not_found",
  "exists": false,
  "message": "❌ Document does NOT exist in Vertex AI Search (deleted or never indexed)",
  "document_id": "c0744c175a37_bitcoin.pdf"
}
```

**If still exists** (deletion failed):
```json
{
  "status": "found",
  "exists": true,
  "message": "✅ Document exists in Vertex AI Search",
  "document": {
    "id": "c0744c175a37_bitcoin.pdf",
    "name": "projects/.../documents/c0744c175a37_bitcoin.pdf",
    "uri": "gs://metatask-documents-bucket/c0744c175a37_bitcoin.pdf",
    "metadata": {
      "collection_id": "...",
      "collection_name": "Research Papers"
    }
  }
}
```

### Method 3: List All Vertex AI Documents

See **all** documents currently in Vertex AI Search:

```bash
curl "http://localhost:8000/debug/vertex-ai-documents"
```

**Response**:
```json
{
  "status": "success",
  "count": 2,
  "documents": [
    {
      "id": "21d12a9d57b818dfb9ef9ffd03f5e37b",
      "name": "projects/.../documents/21d12a9d57b818dfb9ef9ffd03f5e37b",
      "gcs_uri": "gs://metatask-documents-bucket/b52281ce8896_DeepSeek_OCR_paper.pdf"
    },
    {
      "id": "ca7625236bf2362f3e467eef67dd0a4",
      "name": "projects/.../documents/ca7625236bf2362f3e467eef67dd0a4",
      "gcs_uri": "gs://metatask-documents-bucket/c0744c175a37_bitcoin.pdf"
    }
  ],
  "note": "Compare the 'id' field here with the 'vertex_ai_doc_id' in your PostgreSQL database. They should match!"
}
```

**After successful deletion**, the deleted document should **NOT appear** in this list!

---

## Complete Verification Workflow

### Step 1: Before Deletion

Check that the document exists in Vertex AI:

```bash
# Get the vertex_ai_doc_id from your database
curl "http://localhost:8000/debug/verify-document/c0744c175a37_bitcoin.pdf"
```

Expected: `"exists": true`

### Step 2: Delete the Document

```bash
curl -X DELETE "http://localhost:8000/documents/{doc_id}?user_id={user_id}"
```

Check the response:
- ✅ `deletion_status.vertex_ai: true` - Deletion command succeeded
- ✅ `vertex_ai_verification.verified: true` - Confirmed document is gone

### Step 3: After Deletion

Verify again that it's gone:

```bash
curl "http://localhost:8000/debug/verify-document/c0744c175a37_bitcoin.pdf"
```

Expected: `"exists": false`

### Step 4: Check Retrieval

Test that the document no longer appears in search results:

```bash
# Query your retrieval agent for the document content
# It should return "document not found" or similar
```

---

## New Verification Methods Added

### In [vertex_ai_importer.py](vertex_ai_importer.py):

1. **`get_document(vertex_ai_doc_id)`** (lines 284-335)
   - Fetches a specific document from Vertex AI
   - Returns `(exists: bool, document_data: dict | None)`
   - Returns `False` if document doesn't exist (404 error)

2. **`verify_deletion(vertex_ai_doc_id)`** (lines 376-391)
   - Checks if a document has been successfully deleted
   - Returns `(deleted: bool, message: str)`
   - `deleted=True` means document is confirmed gone

### In [main.py](main.py):

1. **Enhanced DELETE endpoint** (lines 861-996)
   - Automatically verifies deletion after deleting
   - Returns `vertex_ai_verification` in response
   - Shows status for all three systems (PostgreSQL, GCS, Vertex AI)

2. **`GET /debug/verify-document/{id}`** (lines 819-858)
   - Standalone verification endpoint
   - Check any document ID at any time
   - Returns existence status and document data

3. **`GET /debug/vertex-ai-documents`** (lines 784-816)
   - Lists all documents in Vertex AI Search
   - Compare with your database to find orphans
   - Useful for debugging ID mismatches

---

## What the Google Documentation Shows

Based on the files in `/Users/tafadzwabwakura/Desktop/search`:

### ✅ Methods Confirmed by Google Docs:

1. **Individual Document Deletion**: ✅ YES
   - REST API: `DELETE /documents/{document_id}`
   - Python SDK: `client.delete_document()`

2. **Bulk Purge**: ✅ YES
   - Python SDK: `client.purge_documents(force=True)`
   - Must set `force=True` to actually delete

3. **Get Document (for verification)**: ✅ YES
   - REST API: `GET /documents/{document_id}`
   - Python SDK: `client.get_document()`

4. **List Documents (for verification)**: ✅ YES
   - REST API: `GET /documents`
   - Python SDK: `client.list_documents()`

### ⚠️ Important Notes from Google Docs:

1. **Document IDs Must Match**: If you use auto-generated IDs during import, you won't know the ID for deletion
2. **Force Flag Required**: For purge operations, `force=False` is a dry-run (doesn't actually delete)
3. **Async Operations**: Deletion may take time to propagate through the index
4. **404 is Normal**: If document was never indexed, deletion returns 404 (not an error)

---

## Troubleshooting Verification Issues

### Issue: Deletion says "success" but document still exists

**Diagnosis**:
```bash
curl "http://localhost:8000/debug/verify-document/{doc_id}"
```

If `exists: true`, the deletion didn't work. Check:
1. Is the document ID correct? (compare with `/debug/vertex-ai-documents`)
2. Check the logs for the exact error message
3. Look for ID mismatch (old documents have wrong IDs)

**Solution**: Run the cleanup script to remove old documents with mismatched IDs.

### Issue: Verification endpoint returns 404 error (not exists: false)

This means the API call itself failed. Check:
1. Vertex AI credentials are correct
2. Data store ID is correct
3. Location is correct (global, us, eu)
4. Network connectivity to Vertex AI API

### Issue: Document gone from Vertex AI but still in search results

**Why**: Search results are cached or index hasn't updated yet.

**Wait time**: Can take 1-5 minutes for index to fully update.

**Verify**:
1. Check `/debug/vertex-ai-documents` - should not appear
2. Check `/debug/verify-document/{id}` - should return `exists: false`
3. Wait a few minutes and try retrieval again

---

## Example: Full Verification Test

```bash
# 1. Upload a test document
curl -X POST "http://localhost:8000/upload" \
  -F "files=@test.pdf" \
  -F "collection_id={collection_id}" \
  -F "user_id={user_id}"

# Response will include vertex_ai_doc_id (e.g., "abc123_test.pdf")

# 2. Verify it exists in Vertex AI
curl "http://localhost:8000/debug/verify-document/abc123_test.pdf"
# Expected: exists: true

# 3. Verify it appears in the list
curl "http://localhost:8000/debug/vertex-ai-documents" | grep "abc123_test.pdf"
# Should find the document

# 4. Delete the document
curl -X DELETE "http://localhost:8000/documents/{doc_id}?user_id={user_id}"
# Check vertex_ai_verification.verified: true

# 5. Verify it's gone
curl "http://localhost:8000/debug/verify-document/abc123_test.pdf"
# Expected: exists: false

# 6. Verify it doesn't appear in the list
curl "http://localhost:8000/debug/vertex-ai-documents" | grep "abc123_test.pdf"
# Should return nothing (not found)

# 7. Test retrieval (should fail)
# Query your retrieval agent - document should not be found
```

---

## Summary

### Question 1: Does the search folder show how to delete?
**Answer**: ✅ **YES!** The folder contains Google's official examples for:
- Individual document deletion (REST API)
- Bulk purge (Python SDK with `force=True`)
- Document verification (get/list operations)

### Question 2: How to confirm deletion actually worked?
**Answer**: ✅ **THREE METHODS NOW AVAILABLE!**
1. **Automatic**: Delete endpoint now returns `vertex_ai_verification` status
2. **Manual Check**: `GET /debug/verify-document/{id}` endpoint
3. **List All**: `GET /debug/vertex-ai-documents` to see all indexed documents

### Key Verification Points:
- ✅ Document should NOT appear in `/debug/vertex-ai-documents`
- ✅ Verify endpoint should return `exists: false`
- ✅ Delete response should show `vertex_ai_verification.verified: true`
- ✅ Retrieval should not return the document

---

## Next Steps

1. Run the cleanup script to remove existing documents with mismatched IDs
2. Upload a new test document
3. Use the verification endpoints to confirm it exists
4. Delete the document
5. Use the verification endpoints to confirm it's gone
6. Test retrieval to ensure it's not searchable

Now you have **complete visibility** into whether deletions are actually working! 🎉
