"""
Quick test script to verify the API is working.

Usage:
    python test_upload.py path/to/document.pdf

This script will:
1. Check health endpoint
2. Upload the specified document
3. Display the response
"""

import sys
import requests
from pathlib import Path


def test_api(file_path: str, api_url: str = "http://localhost:8000"):
    """Test the document upload API."""

    print(f"Testing API at: {api_url}")
    print("-" * 60)

    # 1. Health check
    print("\n1. Checking API health...")
    try:
        response = requests.get(f"{api_url}/health")
        response.raise_for_status()
        print("✅ API is healthy!")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return

    # 2. Upload document
    print(f"\n2. Uploading document: {file_path}")
    file_path_obj = Path(file_path)

    if not file_path_obj.exists():
        print(f"❌ File not found: {file_path}")
        return

    # Determine content type
    content_type_map = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".txt": "text/plain",
        ".html": "text/html",
        ".htm": "text/html",
    }
    content_type = content_type_map.get(file_path_obj.suffix.lower(), "application/octet-stream")

    try:
        with open(file_path, "rb") as f:
            files = {"files": (file_path_obj.name, f, content_type)}
            response = requests.post(f"{api_url}/upload", files=files)

        if response.status_code == 202:
            print("✅ Upload successful!")
            result = response.json()
            print(f"\n📄 Response:")
            print(f"   Status: {result.get('status')}")
            print(f"   Message: {result.get('message')}")

            if result.get("documents"):
                print(f"\n📦 Uploaded Documents:")
                for doc in result["documents"]:
                    print(f"   - ID: {doc['document_id']}")
                    print(f"     GCS URI: {doc['gcs_uri']}")
                    print(f"     Size: {doc['size_bytes']} bytes")

            if result.get("vertex_ai_import"):
                import_info = result["vertex_ai_import"]
                print(f"\n🔄 Vertex AI Import:")
                print(f"   Triggered: {import_info['triggered']}")
                if import_info.get("operation_name"):
                    print(f"   Operation: {import_info['operation_name']}")
                print(f"   Status: {import_info['status_message']}")

            if result.get("failed_uploads"):
                print(f"\n⚠️  Failed Uploads:")
                for failed in result["failed_uploads"]:
                    print(f"   - {failed['filename']}: {failed['error']}")

        else:
            print(f"❌ Upload failed with status {response.status_code}")
            print(f"   Response: {response.text}")

    except Exception as e:
        print(f"❌ Upload failed: {e}")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python test_upload.py <path_to_document>")
        print("\nExample:")
        print("  python test_upload.py document.pdf")
        print("  python test_upload.py sample.docx")
        sys.exit(1)

    file_path = sys.argv[1]
    api_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8000"

    test_api(file_path, api_url)


if __name__ == "__main__":
    main()
