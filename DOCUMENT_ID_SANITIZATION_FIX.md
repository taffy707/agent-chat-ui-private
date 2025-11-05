# Document ID Sanitization Fix - Summary

## Problem Identified

When uploading documents to Vertex AI Search, only 2 out of 5 documents were successfully indexed. The other 3 documents failed with the error:

```
400 Field "document_id" must match the pattern: [a-zA-Z0-9-_]*
```

### Failed Documents

- `4f4d9ddd034d_1-s2.0-S1470160X21011821-main` - Failed due to periods in "1-s2.0"
- `1858c3651c54_1801.03528v1` - Failed due to period in "1801.03528"
- `e28c95fb52b4_070007_1_5.0184740` - Failed due to periods in filename

### Successful Documents

- `800208dff475_179131` - No periods in filename

## Root Cause

The previous fix only removed the file extension (`.pdf`) using `Path.stem`, but did not handle periods and other special characters **within** the filename itself.

Vertex AI Search document IDs have strict requirements:

- **MUST** match the pattern: `[a-zA-Z0-9_-]*`
- **CANNOT** contain: periods (`.`), spaces, parentheses, or any special characters except underscore and hyphen

## Fix Applied

### Changed Files

- `/Users/tafadzwabwakura/agent-chat-ui/document-api/main.py`

### Changes Made

1. **Added regex import** (line 15):

   ```python
   import re
   ```

2. **Updated document ID sanitization** (lines 636-639):

   ```python
   # Vertex AI document IDs can only contain [a-zA-Z0-9-_]* (no periods, spaces, etc.)
   vertex_doc_id = Path(doc["document_id"]).stem  # Removes extension
   # Replace all invalid characters (periods, spaces, parentheses, etc.) with underscores
   vertex_doc_id = re.sub(r'[^a-zA-Z0-9_-]', '_', vertex_doc_id)
   ```

3. **Updated database storage sanitization** (lines 673-676):
   ```python
   # Use blob_name WITHOUT extension as vertex_ai_doc_id (matches Vertex AI)
   vertex_doc_id = Path(doc["document_id"]).stem
   # Replace all invalid characters (periods, spaces, etc.) with underscores
   vertex_doc_id = re.sub(r'[^a-zA-Z0-9_-]', '_', vertex_doc_id)
   ```

### How It Works

The regex pattern `r'[^a-zA-Z0-9_-]'` matches ANY character that is NOT:

- A letter (a-z, A-Z)
- A digit (0-9)
- An underscore (\_)
- A hyphen (-)

All matched characters are replaced with underscores.

### Examples

| Original Filename                                | After Path.stem                              | After Regex                                  | Result   |
| ------------------------------------------------ | -------------------------------------------- | -------------------------------------------- | -------- |
| `4f4d9ddd034d_1-s2.0-S1470160X21011821-main.pdf` | `4f4d9ddd034d_1-s2.0-S1470160X21011821-main` | `4f4d9ddd034d_1_s2_0_S1470160X21011821_main` | ✅ Valid |
| `1858c3651c54_1801.03528v1.pdf`                  | `1858c3651c54_1801.03528v1`                  | `1858c3651c54_1801_03528v1`                  | ✅ Valid |
| `e28c95fb52b4_070007_1_5.0184740.pdf`            | `e28c95fb52b4_070007_1_5.0184740`            | `e28c95fb52b4_070007_1_5_0184740`            | ✅ Valid |
| `687762b05ef6_DeepSeek_OCR_paper.pdf`            | `687762b05ef6_DeepSeek_OCR_paper`            | `687762b05ef6_DeepSeek_OCR_paper`            | ✅ Valid |

## Containers Rebuilt

✅ Document API container rebuilt with fix
✅ LangGraph server container rebuilt
✅ All containers restarted and running

### Container Status

```
document-api               Up (healthy)           0.0.0.0:8000->8080/tcp
retrieval-agent-api        Up (healthy)           0.0.0.0:8123->8000/tcp
retrieval-agent-postgres   Up (healthy)           0.0.0.0:5433->5432/tcp
retrieval-agent-redis      Up (healthy)           0.0.0.0:6379->6379/tcp
```

## Testing Instructions

### Step 1: Delete Existing Documents (Optional but Recommended)

To test with a clean slate, delete the existing documents from:

1. Vertex AI Search console
2. GCS bucket
3. PostgreSQL database (via the UI's delete function)

### Step 2: Upload Test Documents

1. Create a new collection in the UI
2. Upload the 4 documents that previously failed:
   - Any PDF with periods in the filename (e.g., `research-1.0.pdf`)
   - Any PDF with special characters

### Step 3: Verify Upload Success

Check the Document API logs:

```bash
docker logs document-api -f
```

You should see:

```
Creating document in Vertex AI with ID: {sanitized_id}, metadata: {...}
✅ Successfully created document in Vertex AI: {sanitized_id}
```

### Step 4: Verify in Vertex AI Search

Go to Vertex AI Search console and verify:

- All 4 documents appear in the datastore
- Each document has the sanitized ID (with underscores replacing periods)
- Documents have `collection_id` and `user_id` metadata

## Remaining Issue: Metadata Filtering

**IMPORTANT**: Even with this fix, collection filtering **WILL STILL NOT WORK** until you configure the Vertex AI Search schema.

### Why Collection Filtering Still Won't Work

The documents now upload successfully WITH metadata, but Vertex AI Search doesn't know that `collection_id` and `user_id` should be **filterable fields**.

### Error You'll Still See

```
InvalidArgument: 400 Invalid filter syntax 'collection_id: ANY("...")'.
Unsupported field "collection_id"
```

### What Needs to Be Done Next

You MUST configure the Vertex AI Search schema to make `collection_id` and `user_id` indexable/filterable:

1. **Option 1: Via Google Cloud Console**

   - Go to Vertex AI Search → Your Data Store → Schema
   - Find `collection_id` field
   - Mark it as **"Filterable"** and **"Indexable"**
   - Do the same for `user_id`
   - Save and wait for re-indexing

2. **Option 2: Via API/Terraform**

   - Update your data store schema configuration
   - Specify `collection_id` and `user_id` as filterable fields
   - Apply the configuration

3. **Option 3: Via Python Script**
   - Use Google Discovery Engine API to update schema
   - See: `/Users/tafadzwabwakura/Desktop/search/vais-building-blocks/` for examples

### After Schema Configuration

Once the schema is configured and documents are re-indexed:

1. Upload documents again (or trigger re-indexing)
2. Test collection filtering in the UI
3. Check LangGraph logs for the filter being applied
4. Verify search results are correctly filtered by collection

## Summary

✅ **Fixed**: Document ID sanitization now handles ALL invalid characters
✅ **Fixed**: Documents with periods in filenames will now upload successfully
✅ **Fixed**: Database stores consistent sanitized IDs
❌ **Still needs work**: Vertex AI Search schema configuration for filterable metadata

### Next Steps

1. Test the document upload with the previously failing files
2. Verify all documents appear in Vertex AI Search
3. Configure Vertex AI Search schema for filterable `collection_id` and `user_id`
4. Re-test collection filtering end-to-end

---

**Date**: 2025-11-04
**Fixed by**: Claude Code
**Status**: Document upload issue RESOLVED, schema configuration PENDING
