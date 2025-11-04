#!/usr/bin/env python3
"""
Delete documents from Vertex AI Search by URI.

This is the REAL solution - we list all documents, find the one matching
the GCS URI, and delete it by its actual hash ID.
"""

from vertex_ai_importer import VertexAIImporter
from config import settings


def delete_document_by_uri(gcs_uri: str) -> tuple[bool, str]:
    """
    Delete a document from Vertex AI Search by its GCS URI.

    This works around the ID mismatch problem by:
    1. Listing all documents
    2. Finding the one with matching URI
    3. Deleting by its actual hash ID

    Args:
        gcs_uri: The GCS URI (e.g., gs://bucket/blob_name.pdf)

    Returns:
        Tuple of (success: bool, message: str)
    """
    vertex_ai = VertexAIImporter(
        project_id=settings.GCP_PROJECT_ID,
        location=settings.VERTEX_AI_LOCATION,
        data_store_id=settings.VERTEX_AI_DATA_STORE_ID,
    )

    # Step 1: List all documents
    all_docs = vertex_ai.list_documents(page_size=1000)

    # Step 2: Find document with matching URI
    matching_doc = None
    for doc in all_docs:
        if doc.get('gcs_uri') == gcs_uri:
            matching_doc = doc
            break

    if not matching_doc:
        return False, f"❌ Document not found in Vertex AI with URI: {gcs_uri}"

    # Step 3: Delete by actual hash ID
    actual_id = matching_doc['id']
    print(f"Found document with URI: {gcs_uri}")
    print(f"Actual Vertex AI ID: {actual_id}")
    print(f"Deleting...")

    success, message = vertex_ai.delete_document(actual_id)

    if success:
        # Verify deletion
        import time
        time.sleep(2)

        # Check if it's really gone
        all_docs_after = vertex_ai.list_documents(page_size=1000)
        still_exists = any(doc['id'] == actual_id for doc in all_docs_after)

        if still_exists:
            return False, f"❌ Delete API returned success but document still exists! ID: {actual_id}"
        else:
            return True, f"✅ Successfully deleted document with URI: {gcs_uri} (ID: {actual_id})"
    else:
        return False, f"❌ Failed to delete: {message}"


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 delete_by_uri.py <gcs_uri>")
        print("Example: python3 delete_by_uri.py gs://bucket/file.pdf")
        sys.exit(1)

    gcs_uri = sys.argv[1]
    success, message = delete_document_by_uri(gcs_uri)

    print(message)
    sys.exit(0 if success else 1)
