#!/usr/bin/env python3
"""
Cleanup script to remove orphaned documents from Vertex AI Search
that have mismatched IDs (auto-generated instead of explicit blob names).

This script:
1. Lists all documents currently in Vertex AI Search
2. Lists all documents in your PostgreSQL database
3. Identifies orphaned documents (in Vertex AI but not in DB)
4. Deletes the orphaned documents from Vertex AI

Use this to clean up after the ID mismatch issue before uploading new documents.
"""

import asyncio
import sys
from vertex_ai_importer import VertexAIImporter
from config import settings
from database import Database


async def main():
    print("🧹 Cleanup Script: Remove Orphaned Documents with Mismatched IDs\n")
    print("=" * 70)

    # Initialize services
    print("\n📋 Initializing services...")
    vertex_ai_importer = VertexAIImporter(
        project_id=settings.GCP_PROJECT_ID,
        location=settings.VERTEX_AI_LOCATION,
        data_store_id=settings.VERTEX_AI_DATA_STORE_ID,
    )

    db = Database()
    await db.connect()

    # Get all documents from Vertex AI
    print("📥 Fetching documents from Vertex AI Search...")
    vertex_ai_docs = vertex_ai_importer.list_documents(page_size=1000)
    print(f"   Found {len(vertex_ai_docs)} documents in Vertex AI Search")

    if not vertex_ai_docs:
        print("\n✅ No documents in Vertex AI Search. Nothing to clean up!")
        await db.disconnect()
        return

    # Display Vertex AI documents
    print("\n📄 Documents in Vertex AI Search:")
    for i, doc in enumerate(vertex_ai_docs, 1):
        print(f"   {i}. ID: {doc['id']}")
        if 'gcs_uri' in doc:
            print(f"      URI: {doc['gcs_uri']}")
        if 'metadata' in doc:
            print(f"      Metadata: {doc['metadata']}")
        print()

    # Get all expected document IDs from PostgreSQL
    print("📥 Fetching expected document IDs from PostgreSQL...")
    query = "SELECT vertex_ai_doc_id, original_filename, gcs_blob_name FROM documents"
    async with db.pool.acquire() as conn:
        rows = await conn.fetch(query)
    expected_ids = {row['vertex_ai_doc_id'] for row in rows}
    print(f"   Found {len(expected_ids)} documents in PostgreSQL")

    if expected_ids:
        print("\n📄 Expected Vertex AI document IDs (from database):")
        for doc_id in sorted(expected_ids):
            print(f"   - {doc_id}")

    # Find orphaned documents (in Vertex AI but not in DB)
    orphaned_docs = [
        doc for doc in vertex_ai_docs
        if doc['id'] not in expected_ids
    ]

    if not orphaned_docs:
        print("\n✅ No orphaned documents found! All Vertex AI documents are in the database.")
        await db.disconnect()
        return

    print(f"\n⚠️  Found {len(orphaned_docs)} ORPHANED documents in Vertex AI Search:")
    print("   (These are in Vertex AI but NOT in your PostgreSQL database)")
    print()

    for i, doc in enumerate(orphaned_docs, 1):
        print(f"   {i}. ID: {doc['id']}")
        if 'gcs_uri' in doc:
            print(f"      URI: {doc['gcs_uri']}")
        print()

    # Confirm deletion
    print("=" * 70)
    response = input(f"\n⚠️  Delete these {len(orphaned_docs)} orphaned documents from Vertex AI? (y/N): ")

    if response.lower() != 'y':
        print("❌ Aborted by user")
        await db.disconnect()
        return

    print(f"\n🗑️  Deleting {len(orphaned_docs)} orphaned documents...\n")

    succeeded = 0
    failed = 0
    errors = []

    for i, doc in enumerate(orphaned_docs, 1):
        doc_id = doc['id']
        print(f"[{i}/{len(orphaned_docs)}] Deleting {doc_id}...", end=" ")

        success, message = vertex_ai_importer.delete_document(doc_id)

        if success:
            print("✅ Deleted")
            succeeded += 1
        else:
            print(f"❌ Failed: {message}")
            failed += 1
            errors.append({
                "id": doc_id,
                "error": message
            })

    # Summary
    print("\n" + "=" * 70)
    print("📊 Cleanup Summary:")
    print(f"   ✅ Successfully deleted: {succeeded}")
    print(f"   ❌ Failed: {failed}")

    if errors:
        print("\n❌ Failed Deletions:")
        for err in errors:
            print(f"   - {err['id']}: {err['error']}")

    print("\n" + "=" * 70)
    print("\n💡 Next Steps:")
    print("   1. Upload new documents using the fixed upload endpoint")
    print("   2. New documents will use explicit IDs matching the blob names")
    print("   3. Deletion should now work correctly!")
    print()

    await db.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
