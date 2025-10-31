# Collections System - Practical Examples

## Real-World Usage Examples

### Example 1: Medical Researcher (Alice)

#### Alice's Collections Setup
```
Alice's Account
├─ 📁 Medical Research (45 documents)
│  ├─ cancer_study_2024.pdf
│  ├─ clinical_trial_results.pdf
│  ├─ patient_data_analysis.xlsx
│  └─ ...42 more files
│
├─ 📁 Grant Applications (8 documents)
│  ├─ nih_grant_proposal.docx
│  ├─ budget_breakdown.xlsx
│  └─ ...6 more files
│
└─ 📁 Teaching Materials (23 documents)
   ├─ biology_101_syllabus.pdf
   ├─ lecture_slides_week1.pdf
   └─ ...21 more files

Total: 3 collections, 76 documents
```

#### Alice's Daily Workflow

**Morning: Upload new research papers**
```bash
# 1. Create collection (if first time)
curl -X POST http://localhost:8000/collections \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alice",
    "name": "Medical Research",
    "description": "Cancer research papers and clinical trial data"
  }'

# Response:
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "Medical Research",
  "document_count": 0
}

# 2. Upload 5 new research papers
curl -X POST http://localhost:8000/upload \
  -F "user_id=alice" \
  -F "collection_id=550e8400-e29b-41d4-a716-446655440001" \
  -F "files=@cancer_study_2024.pdf" \
  -F "files=@clinical_trial.pdf" \
  -F "files=@patient_data.xlsx"

# Response:
{
  "status": "accepted",
  "collection_name": "Medical Research",
  "documents": [...]
}
```

**Afternoon: Review medical research documents only**
```bash
# List only medical research documents
curl "http://localhost:8000/collections/550e8400-e29b-41d4-a716-446655440001/documents?user_id=alice"

# Response:
{
  "collection_name": "Medical Research",
  "total_count": 45,
  "documents": [
    {
      "filename": "cancer_study_2024.pdf",
      "upload_date": "2025-10-31T09:30:00Z",
      "file_size_bytes": 2457600,
      ...
    },
    ...
  ]
}
```

**Evening: Search across ALL documents**
```bash
# View all documents across all collections
curl "http://localhost:8000/documents?user_id=alice&limit=100"

# Response shows documents from all 3 collections:
{
  "user_id": "alice",
  "total_count": 76,
  "documents": [
    {
      "filename": "cancer_study_2024.pdf",
      "collection_name": "Medical Research",  ← Shows collection
      ...
    },
    {
      "filename": "nih_grant_proposal.docx",
      "collection_name": "Grant Applications",  ← Different collection
      ...
    },
    {
      "filename": "biology_101_syllabus.pdf",
      "collection_name": "Teaching Materials",
      ...
    }
  ]
}
```

**End of Project: Delete entire collection**
```bash
# Delete "Grant Applications" after grant is submitted
curl -X DELETE "http://localhost:8000/collections/550e8400-e29b-41d4-a716-446655440002?user_id=alice"

# Response:
{
  "status": "success",
  "message": "Collection and 8 documents deleted successfully",
  "deleted": {
    "collection_name": "Grant Applications",
    "documents_deleted": 8,
    "gcs_files_deleted": 8,
    "vertex_ai_queued": 8
  }
}

# Now Alice has: 2 collections, 68 documents
```

---

### Example 2: Food Blogger (Bob)

#### Bob's Collections Setup
```
Bob's Account
├─ 📁 Italian Recipes (87 documents)
│  ├─ pasta_carbonara.pdf
│  ├─ tiramisu_recipe.pdf
│  ├─ margherita_pizza.pdf
│  └─ ...84 more files
│
├─ 📁 Asian Cuisine (62 documents)
│  ├─ pad_thai.pdf
│  ├─ sushi_guide.pdf
│  └─ ...60 more files
│
├─ 📁 Baking (43 documents)
│  ├─ sourdough_bread.pdf
│  ├─ chocolate_cake.pdf
│  └─ ...41 more files
│
└─ 📁 Restaurant Reviews (15 documents)
   ├─ michelin_2024.pdf
   └─ ...14 more files

Total: 4 collections, 207 documents
```

#### Bob's Blog Post Workflow

**Step 1: View all collections**
```bash
curl "http://localhost:8000/collections?user_id=bob"

# Response:
{
  "user_id": "bob",
  "total_count": 4,
  "collections": [
    {
      "id": "collection-1",
      "name": "Italian Recipes",
      "description": "Traditional Italian cooking",
      "document_count": 87,
      "created_at": "2025-01-15T10:00:00Z"
    },
    {
      "id": "collection-2",
      "name": "Asian Cuisine",
      "document_count": 62,
      "created_at": "2025-02-20T14:30:00Z"
    },
    {
      "id": "collection-3",
      "name": "Baking",
      "document_count": 43,
      "created_at": "2025-03-10T09:15:00Z"
    },
    {
      "id": "collection-4",
      "name": "Restaurant Reviews",
      "document_count": 15,
      "created_at": "2025-10-01T16:45:00Z"
    }
  ]
}
```

**Step 2: Create new collection for upcoming series**
```bash
curl -X POST http://localhost:8000/collections \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "bob",
    "name": "Mexican Cuisine",
    "description": "Authentic Mexican recipes for new blog series"
  }'

# Now Bob has 5 collections
```

**Step 3: Upload recipes to specific collection**
```bash
# Upload to "Mexican Cuisine" collection
curl -X POST http://localhost:8000/upload \
  -F "user_id=bob" \
  -F "collection_id=collection-5" \
  -F "files=@tacos_al_pastor.pdf" \
  -F "files=@guacamole.pdf" \
  -F "files=@churros.pdf"
```

**Step 4: Search specific collection for blog post**
```bash
# Bob is writing about Italian desserts
curl "http://localhost:8000/collections/collection-1/documents?user_id=bob&limit=100"

# Only sees Italian recipes (87 docs), not Asian or Baking
```

**Step 5: Delete old collection**
```bash
# Bob stops doing restaurant reviews
curl -X DELETE "http://localhost:8000/collections/collection-4?user_id=bob"

# All 15 restaurant review docs deleted from:
# - PostgreSQL ✓
# - Google Cloud Storage ✓
# - Vertex AI Search (queued) ✓
```

---

### Example 3: Project Manager (Charlie)

#### Charlie's Collections Setup
```
Charlie's Account
├─ 📁 Project Alpha - Q1 2025 (156 documents)
│  ├─ project_charter.pdf
│  ├─ technical_specs.docx
│  ├─ budget_q1.xlsx
│  └─ ...153 more files
│
├─ 📁 Project Beta - Q2 2025 (89 documents)
│  ├─ requirements_doc.pdf
│  ├─ design_mockups.pdf
│  └─ ...87 more files
│
├─ 📁 HR Documents (12 documents)
│  ├─ employee_handbook.pdf
│  ├─ benefits_2025.pdf
│  └─ ...10 more files
│
└─ 📁 Personal (8 documents)
   ├─ tax_documents_2024.pdf
   └─ ...7 more files

Total: 4 collections, 265 documents
```

#### Charlie's Project Cleanup Scenario

**Quarterly Review: Project Alpha Completed**

```bash
# 1. Review Project Alpha documents
curl "http://localhost:8000/collections/project-alpha-id/documents?user_id=charlie&limit=200"

# Charlie sees 156 documents related to Project Alpha

# 2. Project is complete, archive and delete
curl -X DELETE "http://localhost:8000/collections/project-alpha-id?user_id=charlie"

# Response:
{
  "status": "success",
  "message": "Collection and 156 documents deleted successfully",
  "deleted": {
    "collection_id": "project-alpha-id",
    "collection_name": "Project Alpha - Q1 2025",
    "documents_deleted": 156,
    "gcs_files_deleted": 156,
    "vertex_ai_deletions_queued": 156
  }
}

# CASCADE deletion means:
# - All 156 documents removed from PostgreSQL
# - All 156 files deleted from GCS bucket
# - All 156 deletion requests queued for Vertex AI
# - Collection record removed
```

**View Remaining Work**
```bash
# Charlie now views all remaining documents
curl "http://localhost:8000/documents?user_id=charlie"

# Response:
{
  "total_count": 109,  ← Down from 265!
  "documents": [
    {
      "filename": "requirements_doc.pdf",
      "collection_name": "Project Beta - Q2 2025",  ← Active project
      ...
    },
    {
      "filename": "employee_handbook.pdf",
      "collection_name": "HR Documents",
      ...
    }
  ]
}

# Only Project Beta, HR, and Personal documents remain
```

---

## API Request/Response Examples

### Complete Workflow: From Scratch

```bash
# ============================================================
# Step 1: User creates first collection
# ============================================================
curl -X POST http://localhost:8000/collections \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alice",
    "name": "Science Papers",
    "description": "Academic research papers in various fields"
  }'

# Response:
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "alice",
  "name": "Science Papers",
  "description": "Academic research papers in various fields",
  "document_count": 0,
  "created_at": "2025-10-31T18:00:00Z",
  "updated_at": "2025-10-31T18:00:00Z"
}

# ============================================================
# Step 2: Upload documents to collection
# ============================================================
curl -X POST http://localhost:8000/upload \
  -F "user_id=alice" \
  -F "collection_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "files=@physics_paper.pdf" \
  -F "files=@chemistry_research.pdf"

# Response:
{
  "status": "accepted",
  "message": "Successfully uploaded 2 document(s) to GCS and triggered indexing",
  "collection_id": "550e8400-e29b-41d4-a716-446655440000",
  "collection_name": "Science Papers",
  "documents": [
    {
      "original_filename": "physics_paper.pdf",
      "document_id": "a1b2c3d4_physics_paper.pdf",
      "gcs_uri": "gs://bucket/a1b2c3d4_physics_paper.pdf",
      "collection_id": "550e8400-e29b-41d4-a716-446655440000",
      "db_id": "doc-uuid-1"
    },
    {
      "original_filename": "chemistry_research.pdf",
      "document_id": "e5f6g7h8_chemistry_research.pdf",
      "gcs_uri": "gs://bucket/e5f6g7h8_chemistry_research.pdf",
      "collection_id": "550e8400-e29b-41d4-a716-446655440000",
      "db_id": "doc-uuid-2"
    }
  ]
}

# ============================================================
# Step 3: List all collections (now shows updated count)
# ============================================================
curl "http://localhost:8000/collections?user_id=alice"

# Response:
{
  "user_id": "alice",
  "total_count": 1,
  "collections": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Science Papers",
      "description": "Academic research papers in various fields",
      "document_count": 2,  ← Updated!
      "created_at": "2025-10-31T18:00:00Z"
    }
  ]
}

# ============================================================
# Step 4: View documents in specific collection
# ============================================================
curl "http://localhost:8000/collections/550e8400-e29b-41d4-a716-446655440000/documents?user_id=alice"

# Response:
{
  "collection_id": "550e8400-e29b-41d4-a716-446655440000",
  "collection_name": "Science Papers",
  "user_id": "alice",
  "total_count": 2,
  "documents": [
    {
      "id": "doc-uuid-1",
      "user_id": "alice",
      "original_filename": "physics_paper.pdf",
      "collection_id": "550e8400-e29b-41d4-a716-446655440000",
      "file_type": ".pdf",
      "file_size_bytes": 2457600,
      "upload_date": "2025-10-31T18:01:00Z"
    },
    {
      "id": "doc-uuid-2",
      "user_id": "alice",
      "original_filename": "chemistry_research.pdf",
      "collection_id": "550e8400-e29b-41d4-a716-446655440000",
      "file_type": ".pdf",
      "file_size_bytes": 1856432,
      "upload_date": "2025-10-31T18:01:00Z"
    }
  ]
}

# ============================================================
# Step 5: Create second collection
# ============================================================
curl -X POST http://localhost:8000/collections \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alice",
    "name": "Food Recipes",
    "description": "Personal cooking recipes"
  }'

# Upload 3 documents to Food Recipes...
# (collection_id: collection-2)

# ============================================================
# Step 6: View ALL documents (across both collections)
# ============================================================
curl "http://localhost:8000/documents?user_id=alice"

# Response:
{
  "user_id": "alice",
  "total_count": 5,  ← 2 from Science + 3 from Food
  "documents": [
    {
      "filename": "physics_paper.pdf",
      "collection_name": "Science Papers",  ← Collection shown
      ...
    },
    {
      "filename": "chemistry_research.pdf",
      "collection_name": "Science Papers",
      ...
    },
    {
      "filename": "pasta_recipe.pdf",
      "collection_name": "Food Recipes",  ← Different collection
      ...
    },
    {
      "filename": "cake_recipe.pdf",
      "collection_name": "Food Recipes",
      ...
    },
    {
      "filename": "soup_recipe.pdf",
      "collection_name": "Food Recipes",
      ...
    }
  ]
}

# ============================================================
# Step 7: Delete entire collection (CASCADE)
# ============================================================
curl -X DELETE "http://localhost:8000/collections/collection-2?user_id=alice"

# Response:
{
  "status": "success",
  "message": "Collection and 3 documents deleted successfully",
  "deleted": {
    "collection_id": "collection-2",
    "collection_name": "Food Recipes",
    "documents_deleted": 3,
    "gcs_files": [
      "pasta_recipe.pdf",
      "cake_recipe.pdf",
      "soup_recipe.pdf"
    ]
  }
}

# ============================================================
# Step 8: Verify deletion
# ============================================================
curl "http://localhost:8000/documents?user_id=alice"

# Response:
{
  "user_id": "alice",
  "total_count": 2,  ← Only Science Papers remain!
  "documents": [
    {
      "filename": "physics_paper.pdf",
      "collection_name": "Science Papers",
      ...
    },
    {
      "filename": "chemistry_research.pdf",
      "collection_name": "Science Papers",
      ...
    }
  ]
}
```

---

## Summary

### Key Benefits of Collections

✅ **Organization** - Group related documents logically
✅ **Isolation** - View only relevant documents when needed
✅ **Bulk Operations** - Delete entire project folders at once
✅ **Clear Hierarchy** - User → Collections → Documents
✅ **Flexible Views** - Browse by collection OR all documents
✅ **Metadata Rich** - Collection name shown with every document

### Perfect For:

- 📚 **Researchers** - Organize by topic/project
- 👨‍🍳 **Content Creators** - Separate different content types
- 💼 **Project Managers** - One collection per project
- 📖 **Students** - Organize by course/subject
- 🏢 **Businesses** - Separate departments/clients

This system provides enterprise-level document organization while maintaining simplicity!
