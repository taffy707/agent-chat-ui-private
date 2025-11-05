# Collections System Design

## Overview

Collections allow users to organize their documents into named libraries (e.g., "Science Papers", "Food Recipes", "Work Documents").

## User Stories

1. **Alice** uploads medical research papers

   - Creates collection: "Medical Research"
   - Uploads 50 PDFs to this collection
   - Can view only medical documents when browsing this collection

2. **Bob** is a food blogger

   - Creates collections: "Italian Recipes", "Asian Cuisine", "Baking"
   - Uploads recipes to appropriate collections
   - Can list all recipes in "Italian Recipes"
   - Deletes "Baking" collection → All baking recipes deleted

3. **Charlie** works on multiple projects
   - Creates: "Project Alpha", "Project Beta", "Personal"
   - Each project has its own document library
   - Can view all documents across all collections
   - Can view documents in a specific collection

## Database Schema

### Collections Table

```sql
CREATE TABLE collections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    document_count INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    UNIQUE(user_id, name)  -- Each user can't have duplicate collection names
);

-- Indexes
CREATE INDEX idx_collections_user_id ON collections(user_id);
CREATE INDEX idx_collections_created_at ON collections(created_at DESC);
```

### Updated Documents Table

```sql
ALTER TABLE documents
ADD COLUMN collection_id UUID REFERENCES collections(id) ON DELETE CASCADE;

-- Index for fast lookups
CREATE INDEX idx_documents_collection_id ON documents(collection_id);
CREATE INDEX idx_documents_user_collection ON documents(user_id, collection_id);
```

**Important**: `ON DELETE CASCADE` means when a collection is deleted, all its documents are automatically deleted.

## API Endpoints

### Collection Management

#### 1. Create Collection

```http
POST /collections
Content-Type: application/json

{
  "user_id": "alice",
  "name": "Medical Research",
  "description": "Collection of medical research papers"
}

Response:
{
  "id": "uuid-123",
  "user_id": "alice",
  "name": "Medical Research",
  "description": "Collection of medical research papers",
  "document_count": 0,
  "created_at": "2025-10-31T10:00:00Z"
}
```

#### 2. List User's Collections

```http
GET /collections?user_id=alice&limit=100&offset=0

Response:
{
  "user_id": "alice",
  "total_count": 3,
  "collections": [
    {
      "id": "uuid-123",
      "name": "Medical Research",
      "description": "...",
      "document_count": 45,
      "created_at": "2025-10-31T10:00:00Z"
    },
    {
      "id": "uuid-456",
      "name": "Personal Notes",
      "document_count": 12,
      "created_at": "2025-10-30T15:30:00Z"
    }
  ]
}
```

#### 3. Get Collection Details

```http
GET /collections/{collection_id}?user_id=alice

Response:
{
  "id": "uuid-123",
  "user_id": "alice",
  "name": "Medical Research",
  "description": "...",
  "document_count": 45,
  "created_at": "2025-10-31T10:00:00Z",
  "updated_at": "2025-10-31T12:00:00Z"
}
```

#### 4. Update Collection

```http
PUT /collections/{collection_id}
Content-Type: application/json

{
  "user_id": "alice",
  "name": "Updated Name",
  "description": "Updated description"
}
```

#### 5. Delete Collection (CASCADE deletes all documents)

```http
DELETE /collections/{collection_id}?user_id=alice

Response:
{
  "status": "success",
  "message": "Collection and 45 documents deleted successfully",
  "deleted": {
    "collection_id": "uuid-123",
    "collection_name": "Medical Research",
    "documents_deleted": 45
  }
}
```

### Document Management (Updated)

#### 6. Upload Documents (Now Requires collection_id)

```http
POST /upload
Content-Type: multipart/form-data

user_id: alice
collection_id: uuid-123
files: [file1.pdf, file2.pdf]

Response:
{
  "status": "accepted",
  "collection_id": "uuid-123",
  "collection_name": "Medical Research",
  "documents": [...]
}
```

#### 7. List Documents in Collection

```http
GET /collections/{collection_id}/documents?user_id=alice&limit=100&offset=0

Response:
{
  "collection_id": "uuid-123",
  "collection_name": "Medical Research",
  "user_id": "alice",
  "total_count": 45,
  "documents": [...]
}
```

#### 8. List ALL User's Documents (Across All Collections) ⭐ NEW

```http
GET /documents?user_id=alice&limit=100&offset=0

Response:
{
  "user_id": "alice",
  "total_count": 120,
  "documents": [
    {
      "id": "doc-1",
      "filename": "research.pdf",
      "collection_id": "uuid-123",
      "collection_name": "Medical Research",
      ...
    },
    {
      "id": "doc-2",
      "filename": "notes.txt",
      "collection_id": "uuid-456",
      "collection_name": "Personal Notes",
      ...
    }
  ]
}
```

#### 9. Delete Document (Unchanged)

```http
DELETE /documents/{doc_id}?user_id=alice
```

## Hierarchy Visualization

```
User: Alice
│
├─ Collection: "Medical Research" (uuid-123)
│  ├─ Document: research_paper_1.pdf
│  ├─ Document: research_paper_2.pdf
│  └─ Document: clinical_trial.pdf
│
├─ Collection: "Personal Notes" (uuid-456)
│  ├─ Document: shopping_list.txt
│  └─ Document: todo.txt
│
└─ Collection: "Work Documents" (uuid-789)
   ├─ Document: project_proposal.docx
   └─ Document: budget.pdf

User: Bob
│
├─ Collection: "Italian Recipes" (uuid-abc)
│  ├─ Document: pasta_carbonara.pdf
│  └─ Document: tiramisu.pdf
│
└─ Collection: "Asian Cuisine" (uuid-def)
   └─ Document: pad_thai.pdf
```

## Workflows

### Workflow 1: User Creates Collection and Uploads Documents

```
1. Alice creates collection "Medical Research"
   POST /collections
   → Returns collection_id: uuid-123

2. Alice uploads 3 PDFs to this collection
   POST /upload
   {
     user_id: "alice",
     collection_id: "uuid-123",
     files: [research1.pdf, research2.pdf, research3.pdf]
   }

3. Alice views documents in this collection
   GET /collections/uuid-123/documents?user_id=alice
   → Returns 3 documents

4. Alice views all her collections
   GET /collections?user_id=alice
   → Returns "Medical Research" with document_count: 3
```

### Workflow 2: User Views All Documents

```
Alice wants to see all her documents across all collections:

GET /documents?user_id=alice

Returns:
{
  "total_count": 57,
  "documents": [
    {
      "filename": "research1.pdf",
      "collection_name": "Medical Research",
      ...
    },
    {
      "filename": "shopping.txt",
      "collection_name": "Personal Notes",
      ...
    },
    ...
  ]
}
```

### Workflow 3: User Deletes Collection (CASCADE)

```
Alice deletes "Medical Research" collection:

DELETE /collections/uuid-123?user_id=alice

System performs:
1. Verify alice owns collection uuid-123 ✓
2. Count documents in collection: 45 documents
3. For each document:
   a. Delete from GCS (specific files)
   b. Add to deletion queue for Vertex AI
   c. Delete from PostgreSQL (CASCADE handles this)
4. Delete collection from PostgreSQL
5. Return summary: "Collection and 45 documents deleted"
```

## Data Integrity Rules

### 1. User Ownership

- Users can only see/modify their own collections
- Users can only see/modify documents in their collections

### 2. Collection Constraints

- Collection names must be unique per user
- Collection names required (cannot be empty)
- Deleting a collection deletes all its documents (CASCADE)

### 3. Document Constraints

- Documents MUST belong to a collection (collection_id NOT NULL)
- Cannot upload documents without specifying collection_id
- Orphaned documents not allowed

### 4. Deletion Order

```
Delete Collection:
  ├─ For each document in collection:
  │  ├─ Delete from GCS
  │  ├─ Queue Vertex AI deletion
  │  └─ Delete from PostgreSQL (CASCADE)
  └─ Delete collection record
```

## Migration Strategy

### For Existing Documents (Without Collections)

If you already have documents in the database without collection_id:

**Option 1: Create Default Collection**

```sql
-- For each user, create a "Default" collection
INSERT INTO collections (user_id, name, description)
SELECT DISTINCT user_id, 'Default Collection', 'Auto-created for existing documents'
FROM documents
WHERE collection_id IS NULL;

-- Assign existing documents to default collection
UPDATE documents d
SET collection_id = (
  SELECT id FROM collections c
  WHERE c.user_id = d.user_id
  AND c.name = 'Default Collection'
)
WHERE collection_id IS NULL;
```

**Option 2: Require Manual Assignment**

```sql
-- Keep collection_id nullable temporarily
ALTER TABLE documents
ADD COLUMN collection_id UUID REFERENCES collections(id) ON DELETE CASCADE;

-- Users must create collections and move documents
-- Then enforce NOT NULL later:
ALTER TABLE documents
ALTER COLUMN collection_id SET NOT NULL;
```

## UI/UX Flow Examples

### Example 1: Document Upload Flow

```
1. User navigates to "Upload Documents"
2. User sees dropdown: "Select Collection"
   - Medical Research (45 docs)
   - Personal Notes (12 docs)
   - [+ Create New Collection]
3. User selects "Medical Research"
4. User uploads 3 PDFs
5. Success: "3 documents uploaded to Medical Research"
```

### Example 2: Browsing Documents

```
Left Sidebar:
- All Documents (120)
- ─────────────
- Collections:
  - Medical Research (45)
  - Personal Notes (12)
  - Work Documents (63)

Main View (when "Medical Research" selected):
- Showing 45 documents in "Medical Research"
- [research_paper_1.pdf] [2.4 MB] [PDF]
- [clinical_trial.pdf] [5.1 MB] [PDF]
- ...
```

### Example 3: Delete Collection Confirmation

```
User clicks delete on "Medical Research":

┌─────────────────────────────────────────┐
│  ⚠️  Delete Collection?                 │
├─────────────────────────────────────────┤
│  Collection: Medical Research           │
│  Documents: 45 files                    │
│                                          │
│  This will permanently delete:          │
│  ✓ The collection                       │
│  ✓ All 45 documents inside it           │
│  ✓ Files from Google Cloud Storage      │
│  ✓ Indexed data from Vertex AI          │
│                                          │
│  This action cannot be undone.          │
│                                          │
│  [Cancel]  [Delete Collection]          │
└─────────────────────────────────────────┘
```

## Performance Considerations

### Indexes for Fast Queries

```sql
-- Fast lookup: User's collections
CREATE INDEX idx_collections_user_id ON collections(user_id);

-- Fast lookup: Documents in a collection
CREATE INDEX idx_documents_collection_id ON documents(collection_id);

-- Fast lookup: User's documents across collections
CREATE INDEX idx_documents_user_collection ON documents(user_id, collection_id);

-- Fast counting
CREATE INDEX idx_documents_user_id ON documents(user_id);
```

### Optimized Queries

```sql
-- Get user's collections with document counts (FAST)
SELECT c.*, COUNT(d.id) as document_count
FROM collections c
LEFT JOIN documents d ON d.collection_id = c.id
WHERE c.user_id = 'alice'
GROUP BY c.id
ORDER BY c.created_at DESC;

-- Get documents in collection (FAST)
SELECT * FROM documents
WHERE collection_id = 'uuid-123'
  AND user_id = 'alice'
ORDER BY upload_date DESC
LIMIT 100;

-- Get all user documents with collection info (FAST)
SELECT d.*, c.name as collection_name
FROM documents d
JOIN collections c ON d.collection_id = c.id
WHERE d.user_id = 'alice'
ORDER BY d.upload_date DESC
LIMIT 100;
```

## Security Considerations

1. **Authorization Checks**

   - Always verify user_id matches collection owner
   - Always verify user_id matches document owner
   - Never expose other users' collections/documents

2. **Validation**

   - Collection names: Max 255 chars, no SQL injection
   - Verify collection exists before upload
   - Verify user owns collection before operations

3. **Rate Limiting**
   - Limit collections per user (e.g., 100 collections)
   - Limit documents per collection (e.g., 10,000 docs)

## Summary

### Key Features

✅ **Collections** - Named document libraries per user
✅ **Hierarchy** - User → Collections → Documents
✅ **CASCADE Delete** - Deleting collection deletes all documents
✅ **Flexible Viewing** - View by collection OR all documents
✅ **Metadata Rich** - Collection name shown with each document
✅ **Fast Queries** - Optimized indexes for performance

### API Summary

| Endpoint                      | Method | Purpose                      |
| ----------------------------- | ------ | ---------------------------- |
| `/collections`                | POST   | Create collection            |
| `/collections`                | GET    | List user's collections      |
| `/collections/{id}`           | GET    | Get collection details       |
| `/collections/{id}`           | PUT    | Update collection            |
| `/collections/{id}`           | DELETE | Delete collection + all docs |
| `/collections/{id}/documents` | GET    | List docs in collection      |
| `/upload`                     | POST   | Upload docs to collection    |
| `/documents`                  | GET    | List ALL user's documents    |
| `/documents/{id}`             | DELETE | Delete single document       |

This design provides a clean, scalable way to organize documents with proper data integrity and security!
