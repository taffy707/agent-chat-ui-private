#!/usr/bin/env python3
"""
Test script to verify Vertex AI Search document operations.

This script tests:
1. Listing all documents in Vertex AI Search
2. Getting specific documents by ID
3. Verifying deletion status
4. Checking for ID mismatches
"""

import sys
from vertex_ai_importer import VertexAIImporter
from config import settings

def main():
    print("=" * 80)
    print("🔍 Vertex AI Search Verification Test")
    print("=" * 80)

    # Initialize Vertex AI importer
    print("\n📋 Initializing Vertex AI Search client...")
    print(f"   Project ID: {settings.GCP_PROJECT_ID}")
    print(f"   Location: {settings.VERTEX_AI_LOCATION}")
    print(f"   Data Store ID: {settings.VERTEX_AI_DATA_STORE_ID}")

    try:
        vertex_ai = VertexAIImporter(
            project_id=settings.GCP_PROJECT_ID,
            location=settings.VERTEX_AI_LOCATION,
            data_store_id=settings.VERTEX_AI_DATA_STORE_ID,
        )
        print("   ✅ Client initialized successfully\n")
    except Exception as e:
        print(f"   ❌ Failed to initialize client: {e}")
        return 1

    # Test 1: List all documents
    print("=" * 80)
    print("TEST 1: List All Documents in Vertex AI Search")
    print("=" * 80)

    try:
        documents = vertex_ai.list_documents(page_size=100)
        print(f"\n✅ Found {len(documents)} document(s) in Vertex AI Search\n")

        if documents:
            for i, doc in enumerate(documents, 1):
                print(f"Document {i}:")
                print(f"  ID: {doc['id']}")
                print(f"  Name: {doc.get('name', 'N/A')}")
                if 'gcs_uri' in doc:
                    print(f"  GCS URI: {doc['gcs_uri']}")
                if 'metadata' in doc:
                    print(f"  Metadata: {doc['metadata']}")
                print()
        else:
            print("📭 No documents found in Vertex AI Search (datastore is empty)")

    except Exception as e:
        print(f"❌ Failed to list documents: {e}")
        return 1

    # Test 2: Test get_document with known IDs from screenshots
    print("\n" + "=" * 80)
    print("TEST 2: Get Specific Documents by ID")
    print("=" * 80)

    # These are the IDs we saw in your screenshots
    test_ids = [
        "21d12a9d57b818dfb9ef9ffd03f5e37b",  # DeepSeek paper (hash ID)
        "ca7625236bf2362f3e467eef67dd0a4",   # Bitcoin paper (hash ID)
        "c0744c175a37_bitcoin.pdf",           # Expected blob name
        "b52281ce8896_DeepSeek_OCR_paper.pdf" # Expected blob name
    ]

    for doc_id in test_ids:
        print(f"\n🔍 Checking document: {doc_id}")
        try:
            exists, doc_data = vertex_ai.get_document(doc_id)

            if exists:
                print(f"   ✅ FOUND in Vertex AI")
                print(f"      ID: {doc_data.get('id')}")
                if 'uri' in doc_data:
                    print(f"      URI: {doc_data['uri']}")
                if 'metadata' in doc_data:
                    print(f"      Metadata: {doc_data['metadata']}")
            else:
                print(f"   ❌ NOT FOUND in Vertex AI")

        except Exception as e:
            print(f"   ⚠️  Error checking document: {e}")

    # Test 3: Verify deletion status
    print("\n" + "=" * 80)
    print("TEST 3: Verify Deletion Status")
    print("=" * 80)

    print("\n🔍 Testing verify_deletion() method on expected blob names...")

    blob_names_to_check = [
        "c0744c175a37_bitcoin.pdf",
        "b52281ce8896_DeepSeek_OCR_paper.pdf"
    ]

    for blob_name in blob_names_to_check:
        print(f"\n📄 {blob_name}:")
        try:
            deleted, message = vertex_ai.verify_deletion(blob_name)
            print(f"   {message}")

            if not deleted:
                print(f"   ⚠️  This document still exists in Vertex AI!")
                print(f"       This is the ID mismatch problem - the blob name doesn't match the Vertex AI ID")
        except Exception as e:
            print(f"   ⚠️  Error: {e}")

    # Summary and recommendations
    print("\n" + "=" * 80)
    print("📊 SUMMARY & ANALYSIS")
    print("=" * 80)

    if len(documents) > 0:
        print(f"\n✅ Total documents in Vertex AI: {len(documents)}")

        # Check for ID mismatches
        print("\n🔍 ID Mismatch Analysis:")

        hash_ids = [doc['id'] for doc in documents if len(doc['id']) == 32]
        blob_ids = [doc['id'] for doc in documents if '_' in doc['id']]

        if hash_ids:
            print(f"   ⚠️  Found {len(hash_ids)} document(s) with HASH IDs (auto-generated):")
            for hash_id in hash_ids:
                print(f"       - {hash_id}")
            print("\n   ❌ These are OLD documents with mismatched IDs!")
            print("   ❌ They CANNOT be deleted using blob names!")
            print("   💡 Run cleanup_mismatched_vertex_ai_docs.py to remove them")

        if blob_ids:
            print(f"\n   ✅ Found {len(blob_ids)} document(s) with BLOB NAME IDs:")
            for blob_id in blob_ids:
                print(f"       - {blob_id}")
            print("\n   ✅ These are NEW documents with correct IDs!")
            print("   ✅ They CAN be deleted using the blob names!")

        if not blob_ids and hash_ids:
            print("\n❗ RECOMMENDATION:")
            print("   1. Run: python cleanup_mismatched_vertex_ai_docs.py")
            print("   2. This will remove all documents with mismatched IDs")
            print("   3. Upload new documents - they will use correct IDs")
            print("   4. Deletion will work correctly!")
    else:
        print("\n✅ Vertex AI Search datastore is EMPTY")
        print("   You can now upload new documents with correct IDs!")

    print("\n" + "=" * 80)
    print("✅ Verification test completed!")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
