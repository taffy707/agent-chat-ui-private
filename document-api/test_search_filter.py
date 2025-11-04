#!/usr/bin/env python3
"""
Test if we can use Search API with filters to find documents by user_id or collection_id.

This would be WAY more efficient than listing all documents!
"""

from google.cloud import discoveryengine_v1alpha as discoveryengine
from google.api_core.client_options import ClientOptions
from config import settings

def search_with_filter(filter_expr: str, query: str = ""):
    """
    Search documents with a filter.

    Args:
        filter_expr: Filter expression (e.g., "user_id='test-user'")
        query: Search query (can be empty for just filtering)
    """
    location = settings.VERTEX_AI_LOCATION

    client_options = (
        ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
        if location != "global"
        else None
    )

    search_client = discoveryengine.SearchServiceClient(client_options=client_options)

    serving_config = search_client.serving_config_path(
        project=settings.GCP_PROJECT_ID,
        location=location,
        data_store=settings.VERTEX_AI_DATA_STORE_ID,
        serving_config="default_config",
    )

    request = discoveryengine.SearchRequest(
        serving_config=serving_config,
        query=query,
        filter=filter_expr,
        page_size=10,
    )

    print(f"Testing filter: {filter_expr}")
    print(f"Query: '{query}' (empty = list all)")
    print("=" * 80)

    try:
        response = search_client.search(request)

        results = list(response.results)
        print(f"\n✅ Search succeeded!")
        print(f"Found {len(results)} results\n")

        for i, result in enumerate(results, 1):
            doc = result.document
            print(f"{i}. Document:")
            print(f"   ID: {doc.id}")
            if hasattr(doc, 'struct_data') and doc.struct_data:
                print(f"   Metadata: {dict(doc.struct_data)}")
            if hasattr(doc.derived_struct_data, 'link'):
                print(f"   Link: {doc.derived_struct_data.link}")
            print()

        return True, results

    except Exception as e:
        print(f"\n❌ Search failed: {e}")
        return False, None


if __name__ == "__main__":
    print("🔍 Testing Search API with Metadata Filters")
    print("=" * 80)
    print()

    # Test 1: Try filtering by user_id
    print("\n📋 TEST 1: Filter by user_id")
    print("-" * 80)
    success, results = search_with_filter("user_id='test-user-deletion-proof'", query="")

    # Test 2: Try with query="*" (match all)
    print("\n📋 TEST 2: Filter by user_id with wildcard query")
    print("-" * 80)
    success, results = search_with_filter("user_id='test-user-deletion-proof'", query="*")

    # Test 3: Try different filter syntax
    print("\n📋 TEST 3: Different filter syntax")
    print("-" * 80)
    success, results = search_with_filter("user_id:test-user-deletion-proof", query="")

    print("\n" + "=" * 80)
    print("Test complete!")
