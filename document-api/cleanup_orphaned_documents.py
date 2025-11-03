#!/usr/bin/env python3
"""
Cleanup script to manually delete orphaned documents from Vertex AI Search.

These are documents that failed to delete from Vertex AI but were removed from
PostgreSQL and GCS.
"""

import asyncio
import sys
from vertex_ai_importer import VertexAIImporter
from config import settings
import asyncpg

async def get_failed_deletions():
    """Get all documents that failed to delete."""
    conn = await asyncpg.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        database=settings.POSTGRES_DB,
    )

    query = """
    SELECT vertex_ai_doc_id, original_filename, attempt_count
    FROM deletion_queue
    WHERE status = 'failed'
    ORDER BY created_at
    """

    rows = await conn.fetch(query)
    await conn.close()

    return [dict(row) for row in rows]


async def delete_orphaned_document(vertex_ai_importer, vertex_ai_doc_id):
    """Attempt to delete a document from Vertex AI."""
    try:
        success, message = vertex_ai_importer.delete_document(vertex_ai_doc_id)
        return success, message
    except Exception as e:
        return False, str(e)


async def clear_deletion_queue():
    """Clear all failed items from deletion queue."""
    conn = await asyncpg.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        database=settings.POSTGRES_DB,
    )

    query = "DELETE FROM deletion_queue WHERE status = 'failed'"
    result = await conn.execute(query)
    await conn.close()

    return result


async def main():
    print("🧹 Cleanup Script: Deleting Orphaned Documents from Vertex AI\n")
    print("=" * 70)

    # Initialize Vertex AI importer
    vertex_ai_importer = VertexAIImporter(
        project_id=settings.GCP_PROJECT_ID,
        location=settings.VERTEX_AI_LOCATION,
        data_store_id=settings.VERTEX_AI_DATA_STORE_ID,
    )

    # Get failed deletions
    print("\n📋 Fetching failed deletions from queue...")
    failed_docs = await get_failed_deletions()

    if not failed_docs:
        print("✅ No orphaned documents found! Queue is clean.")
        return

    print(f"Found {len(failed_docs)} orphaned documents:\n")

    for i, doc in enumerate(failed_docs, 1):
        print(f"{i}. {doc['vertex_ai_doc_id']}")
        if doc['original_filename']:
            print(f"   Filename: {doc['original_filename']}")
        print(f"   Failed attempts: {doc['attempt_count']}")
        print()

    # Confirm deletion
    response = input(f"\n⚠️  Attempt to delete these {len(failed_docs)} documents from Vertex AI? (y/N): ")

    if response.lower() != 'y':
        print("❌ Aborted by user")
        return

    print(f"\n🗑️  Attempting to delete {len(failed_docs)} documents...\n")

    succeeded = 0
    still_not_found = 0
    failed = 0

    for i, doc in enumerate(failed_docs, 1):
        vertex_ai_doc_id = doc['vertex_ai_doc_id']
        print(f"[{i}/{len(failed_docs)}] Deleting {vertex_ai_doc_id}...", end=" ")

        success, message = await delete_orphaned_document(vertex_ai_importer, vertex_ai_doc_id)

        if success:
            print("✅ Deleted")
            succeeded += 1
        elif "404" in message or "does not exist" in message.lower():
            print("⚠️  Not found (already gone or never indexed)")
            still_not_found += 1
        else:
            print(f"❌ Failed: {message}")
            failed += 1

    # Summary
    print("\n" + "=" * 70)
    print("📊 Cleanup Summary:")
    print(f"   ✅ Successfully deleted: {succeeded}")
    print(f"   ⚠️  Not found (OK): {still_not_found}")
    print(f"   ❌ Failed: {failed}")
    print()

    # Clear queue
    if succeeded > 0 or still_not_found > 0:
        response = input("🧹 Clear failed items from deletion queue? (Y/n): ")
        if response.lower() != 'n':
            result = await clear_deletion_queue()
            print(f"✅ Cleared deletion queue: {result}")
        else:
            print("⚠️  Queue not cleared (items remain for manual review)")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        sys.exit(1)
