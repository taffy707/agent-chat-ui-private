#!/usr/bin/env python3
"""
Force delete a specific document from Vertex AI Search.
"""

import sys
from vertex_ai_importer import VertexAIImporter
from config import settings

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 force_delete_document.py <vertex_ai_doc_id>")
        sys.exit(1)

    vertex_ai_doc_id = sys.argv[1]
    print(f"🗑️  Attempting to delete: {vertex_ai_doc_id}")

    # Initialize Vertex AI importer
    vertex_ai_importer = VertexAIImporter(
        project_id=settings.GCP_PROJECT_ID,
        location=settings.VERTEX_AI_LOCATION,
        data_store_id=settings.VERTEX_AI_DATA_STORE_ID,
    )

    try:
        success, message = vertex_ai_importer.delete_document(vertex_ai_doc_id)

        if success:
            print(f"✅ Successfully deleted: {vertex_ai_doc_id}")
            print(f"   Message: {message}")
            return 0
        else:
            print(f"❌ Failed to delete: {vertex_ai_doc_id}")
            print(f"   Error: {message}")
            return 1
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
