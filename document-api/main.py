"""
FastAPI Document Upload Service for Vertex AI Search.

This service accepts document uploads, stores them in Google Cloud Storage,
and triggers Vertex AI Search to automatically process and index them.

Based on patterns from:
- cloud-function/python/main.py (API structure)
- vais-building-blocks/ingesting_unstructured_documents_with_metadata.ipynb (upload workflow)
- create_datastore_and_search.ipynb (import patterns)
"""

import asyncio
import logging
import re
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from config import settings
from database import db
from deletion_queue import DeletionQueue
from gcs_uploader import GCSUploader
from vertex_ai_importer import VertexAIImporter
from index_status_worker import IndexStatusWorker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
)

# Configure CORS - Allow requests from your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React default
        "http://localhost:5173",  # Vite default
        "http://localhost:4200",  # Angular default
        # Add your production frontend URL here when deploying
        # "https://your-frontend-domain.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Initialize services
gcs_uploader = GCSUploader(
    project_id=settings.GCP_PROJECT_ID, bucket_name=settings.GCS_BUCKET_NAME
)

vertex_ai_importer = VertexAIImporter(
    project_id=settings.GCP_PROJECT_ID,
    location=settings.VERTEX_AI_LOCATION,
    data_store_id=settings.VERTEX_AI_DATA_STORE_ID,
)

# Initialize background workers (will be fully initialized on startup)
deletion_queue = None
index_status_worker = None


@app.on_event("startup")
async def startup_event():
    """Run startup checks."""
    global deletion_queue, index_status_worker

    logger.info("Starting Document Upload API...")
    logger.info(f"GCP Project: {settings.GCP_PROJECT_ID}")
    logger.info(f"Datastore ID: {settings.VERTEX_AI_DATA_STORE_ID}")
    logger.info(f"GCS Bucket: {settings.GCS_BUCKET_NAME}")

    # Connect to database
    await db.connect()
    await db.initialize_schema()

    # Initialize deletion queue
    deletion_queue = DeletionQueue(db.pool, vertex_ai_importer)
    await deletion_queue.initialize_schema()

    # Initialize index status worker
    index_status_worker = IndexStatusWorker(vertex_ai_importer)

    # Start background workers
    asyncio.create_task(deletion_queue.start_background_worker(interval_seconds=60))
    asyncio.create_task(index_status_worker.start_background_worker(interval_seconds=120))

    # Ensure bucket exists
    if not gcs_uploader.ensure_bucket_exists():
        logger.warning(
            f"Could not verify bucket {settings.GCS_BUCKET_NAME}. "
            "Make sure it exists or the service account has permissions to create it."
        )


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    if deletion_queue:
        await deletion_queue.stop_background_worker()
    await db.disconnect()
    logger.info("Shut down complete")


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API information."""
    return {
        "service": settings.API_TITLE,
        "version": settings.API_VERSION,
        "status": "running",
        "endpoints": {
            "health": "/health",
            "upload": "/upload (POST)",
            "docs": "/docs",
        },
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "gcp_project": settings.GCP_PROJECT_ID,
        "datastore_id": settings.VERTEX_AI_DATA_STORE_ID,
        "bucket": settings.GCS_BUCKET_NAME,
    }


# ============================================================
# Collection Management Endpoints
# ============================================================

@app.post("/collections", tags=["Collections"], status_code=status.HTTP_201_CREATED)
async def create_collection(
    user_id: str = Form(..., description="User ID who owns the collection"),
    name: str = Form(..., description="Collection name"),
    description: Optional[str] = Form(None, description="Optional collection description"),
):
    """
    Create a new collection for organizing documents.

    Collections allow users to group related documents together
    (e.g., "Medical Research", "Work Documents", "Personal Files").

    Args:
        user_id: User identifier
        name: Collection name (must be unique per user)
        description: Optional description

    Returns:
        Created collection with ID and metadata
    """
    try:
        collection_id = await db.create_collection(user_id, name, description)
        collection = await db.get_collection_by_id(collection_id, user_id)

        # Convert datetime to string
        if collection:
            collection["id"] = str(collection["id"])
            if collection.get("created_at"):
                collection["created_at"] = collection["created_at"].isoformat()
            if collection.get("updated_at"):
                collection["updated_at"] = collection["updated_at"].isoformat()

        return collection

    except Exception as e:
        logger.error(f"Error creating collection: {str(e)}")
        if "unique constraint" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Collection '{name}' already exists for this user",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create collection: {str(e)}",
        )


@app.get("/collections", tags=["Collections"])
async def list_collections(
    user_id: str = Query(..., description="User ID to list collections for"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum collections to return"),
    offset: int = Query(0, ge=0, description="Number of collections to skip"),
):
    """
    List all collections for a user with document counts.

    Args:
        user_id: User identifier
        limit: Maximum collections to return
        offset: Pagination offset

    Returns:
        List of collections with document counts
    """
    try:
        collections = await db.list_collections(user_id, limit, offset)
        total_count = await db.count_user_collections(user_id)

        # Convert datetime and UUID to strings
        for collection in collections:
            collection["id"] = str(collection["id"])
            if collection.get("created_at"):
                collection["created_at"] = collection["created_at"].isoformat()
            if collection.get("updated_at"):
                collection["updated_at"] = collection["updated_at"].isoformat()

        return {
            "user_id": user_id,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "returned_count": len(collections),
            "collections": collections,
        }

    except Exception as e:
        logger.error(f"Error listing collections for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list collections: {str(e)}",
        )


@app.get("/collections/{collection_id}", tags=["Collections"])
async def get_collection(
    collection_id: UUID,
    user_id: str = Query(..., description="User ID for ownership verification"),
):
    """
    Get details of a specific collection.

    Args:
        collection_id: Collection UUID
        user_id: User ID for ownership verification

    Returns:
        Collection details with document count
    """
    try:
        collection = await db.get_collection_by_id(collection_id, user_id)

        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection {collection_id} not found or you don't have access",
            )

        # Convert datetime and UUID to strings
        collection["id"] = str(collection["id"])
        if collection.get("created_at"):
            collection["created_at"] = collection["created_at"].isoformat()
        if collection.get("updated_at"):
            collection["updated_at"] = collection["updated_at"].isoformat()

        return collection

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting collection {collection_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get collection: {str(e)}",
        )


@app.get("/collections/{collection_id}/documents", tags=["Collections"])
async def list_collection_documents(
    collection_id: UUID,
    user_id: str = Query(..., description="User ID for ownership verification"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum documents to return"),
    offset: int = Query(0, ge=0, description="Number of documents to skip"),
):
    """
    List all documents in a specific collection.

    Args:
        collection_id: Collection UUID
        user_id: User ID for ownership verification
        limit: Maximum documents to return
        offset: Pagination offset

    Returns:
        List of documents in the collection
    """
    try:
        # Verify collection exists and user owns it
        collection = await db.get_collection_by_id(collection_id, user_id)
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection {collection_id} not found or you don't have access",
            )

        # Get documents
        documents = await db.list_documents_by_collection(
            collection_id, user_id, limit, offset
        )
        total_count = await db.count_collection_documents(collection_id, user_id)

        # Convert datetime and UUID to strings
        for doc in documents:
            doc["id"] = str(doc["id"])
            doc["collection_id"] = str(doc["collection_id"])
            if doc.get("upload_date"):
                doc["upload_date"] = doc["upload_date"].isoformat()
            if doc.get("created_at"):
                doc["created_at"] = doc["created_at"].isoformat()
            if doc.get("updated_at"):
                doc["updated_at"] = doc["updated_at"].isoformat()

        return {
            "collection_id": str(collection_id),
            "collection_name": collection["name"],
            "user_id": user_id,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "returned_count": len(documents),
            "documents": documents,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error listing documents for collection {collection_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}",
        )


@app.delete("/collections/{collection_id}", tags=["Collections"])
async def delete_collection(
    collection_id: UUID,
    user_id: str = Query(..., description="User ID for ownership verification"),
):
    """
    Delete a collection and ALL its documents (CASCADE delete).

    This will:
    1. Delete all documents from PostgreSQL (CASCADE)
    2. Delete all files from Google Cloud Storage
    3. Queue Vertex AI deletions for all documents
    4. Delete the collection record

    WARNING: This action cannot be undone!

    Args:
        collection_id: Collection UUID
        user_id: User ID for ownership verification

    Returns:
        Deletion summary with counts
    """
    try:
        # Get collection and documents before deleting
        collection = await db.get_collection_by_id(collection_id, user_id)
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Collection {collection_id} not found or you don't have access",
            )

        # Get all documents in collection (for GCS/Vertex AI cleanup)
        documents = await db.list_documents_by_collection(
            collection_id, user_id, limit=10000, offset=0
        )

        # Delete from GCS and queue Vertex AI deletions
        gcs_deleted_count = 0
        vertex_ai_queued_count = 0

        for doc in documents:
            # Delete from GCS
            try:
                gcs_uploader.delete_file(doc["gcs_blob_name"])
                gcs_deleted_count += 1
            except Exception as e:
                logger.error(f"Failed to delete from GCS: {doc['gcs_blob_name']} - {e}")

            # Delete from Vertex AI using URI (reliable method)
            try:
                vertex_ai_success, vertex_ai_msg = vertex_ai_importer.delete_document_by_uri(
                    gcs_uri=doc["gcs_uri"]
                )
                if vertex_ai_success:
                    logger.info(f"✅ Deleted from Vertex AI: {doc['vertex_ai_doc_id']}")
                else:
                    # Queue for retry
                    await deletion_queue.enqueue_deletion(
                        vertex_ai_doc_id=doc["vertex_ai_doc_id"],
                        user_id=user_id,
                        original_filename=doc["original_filename"],
                    )
                    vertex_ai_queued_count += 1
            except Exception as e:
                # Queue for retry
                await deletion_queue.enqueue_deletion(
                    vertex_ai_doc_id=doc["vertex_ai_doc_id"],
                    user_id=user_id,
                    original_filename=doc["original_filename"],
                )
                vertex_ai_queued_count += 1

        # Delete collection (CASCADE deletes documents from PostgreSQL)
        success, doc_count = await db.delete_collection(collection_id, user_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete collection from database",
            )

        return {
            "status": "success",
            "message": f"Collection '{collection['name']}' and {doc_count} documents deleted successfully",
            "deleted": {
                "collection_id": str(collection_id),
                "collection_name": collection["name"],
                "documents_deleted_from_db": doc_count,
                "files_deleted_from_gcs": gcs_deleted_count,
                "vertex_ai_deletions_queued": vertex_ai_queued_count,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting collection {collection_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete collection: {str(e)}",
        )


def validate_file(file: UploadFile) -> tuple[bool, str]:
    """
    Validate uploaded file.

    Args:
        file: FastAPI UploadFile object

    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    # Check file extension
    file_path = Path(file.filename)
    file_extension = file_path.suffix.lower()

    if file_extension not in settings.ALLOWED_EXTENSIONS:
        return False, (
            f"Invalid file type: {file_extension}. "
            f"Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # Check MIME type
    if file.content_type not in settings.ALLOWED_MIME_TYPES:
        return False, (
            f"Invalid MIME type: {file.content_type}. "
            f"Allowed types: {', '.join(settings.ALLOWED_MIME_TYPES)}"
        )

    return True, ""


@app.post("/upload", tags=["Documents"], status_code=status.HTTP_202_ACCEPTED)
async def upload_documents(
    user_id: str = Form(..., description="User ID who owns the document"),
    collection_id: UUID = Form(..., description="Collection ID where documents will be stored"),
    files: List[UploadFile] = File(...),
):
    """
    Upload documents to a collection and trigger Vertex AI Search indexing.

    Workflow:
    1. Verify collection exists and user owns it
    2. Validate file types and sizes
    3. Upload files to Google Cloud Storage
    4. Trigger Vertex AI Search import (automatic processing)
    5. Save document metadata to PostgreSQL with collection_id
    6. Return upload status with document IDs

    Vertex AI Search will automatically:
    - Extract text from PDF/DOCX/HTML
    - Chunk documents optimally
    - Generate embeddings
    - Index for search

    Args:
        user_id: User identifier who owns the documents
        collection_id: Collection UUID where documents will be stored
        files: List of files to upload (PDF, DOCX, TXT, HTML)

    Returns:
        JSON response with upload status and document information

    Raises:
        HTTPException: If validation fails or upload errors occur
    """
    # Verify collection exists and user owns it
    collection = await db.get_collection_by_id(collection_id, user_id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection {collection_id} not found or you don't have access",
        )
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided. Please upload at least one file.",
        )

    logger.info(f"Received upload request for {len(files)} file(s)")

    uploaded_documents = []
    failed_uploads = []
    gcs_uris = []

    # Process each file
    for file in files:
        try:
            # Validate file
            is_valid, error_message = validate_file(file)
            if not is_valid:
                logger.warning(f"Validation failed for {file.filename}: {error_message}")
                failed_uploads.append(
                    {"filename": file.filename, "error": error_message}
                )
                continue

            # Read file content
            file_content = await file.read()
            file_size = len(file_content)

            # Check file size
            if file_size > settings.MAX_FILE_SIZE:
                error_msg = (
                    f"File size ({file_size} bytes) exceeds maximum "
                    f"allowed size ({settings.MAX_FILE_SIZE} bytes)"
                )
                logger.warning(f"Size check failed for {file.filename}: {error_msg}")
                failed_uploads.append({"filename": file.filename, "error": error_msg})
                continue

            # Upload to GCS with collection metadata
            try:
                # Prepare GCS metadata for collection filtering
                gcs_metadata = {
                    "collection_id": str(collection_id),
                    "collection_name": collection["name"],
                    "user_id": user_id,
                    "original_filename": file.filename,
                }

                gcs_uri, blob_name = gcs_uploader.upload_file(
                    file_content=file_content,
                    original_filename=file.filename,
                    content_type=file.content_type,
                    metadata=gcs_metadata,
                )

                gcs_uris.append(gcs_uri)

                # Store file extension
                file_extension = Path(file.filename).suffix.lower()

                uploaded_documents.append(
                    {
                        "original_filename": file.filename,
                        "document_id": blob_name,
                        "gcs_uri": gcs_uri,
                        "gcs_blob_name": blob_name,
                        "size_bytes": file_size,
                        "content_type": file.content_type,
                        "file_type": file_extension,
                    }
                )
                logger.info(f"Successfully uploaded {file.filename} to {gcs_uri}")

            except Exception as e:
                error_msg = f"Failed to upload to GCS: {str(e)}"
                logger.error(f"GCS upload error for {file.filename}: {error_msg}")
                failed_uploads.append({"filename": file.filename, "error": error_msg})

        except Exception as e:
            error_msg = f"Unexpected error processing file: {str(e)}"
            logger.error(f"Processing error for {file.filename}: {error_msg}")
            failed_uploads.append({"filename": file.filename, "error": error_msg})

    # Check if any files were successfully uploaded
    if not gcs_uris:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "No files were successfully uploaded",
                "failed_uploads": failed_uploads,
            },
        )

    # Import documents to Vertex AI Search with metadata (for collection filtering)
    # Using create_document_with_id instead of bulk import to preserve metadata
    import_successes = []
    import_failures = []

    for doc in uploaded_documents:
        try:
            # Prepare metadata for Vertex AI Search filtering
            vertex_metadata = {
                "collection_id": str(collection_id),
                "collection_name": collection["name"],
                "user_id": user_id,
                "original_filename": doc["original_filename"],
            }

            # Vertex AI document IDs can only contain [a-zA-Z0-9-_]* (no periods, spaces, etc.)
            vertex_doc_id = Path(doc["document_id"]).stem  # Removes extension
            # Replace all invalid characters (periods, spaces, parentheses, etc.) with underscores
            vertex_doc_id = re.sub(r'[^a-zA-Z0-9_-]', '_', vertex_doc_id)

            logger.info(f"Creating document in Vertex AI with ID: {vertex_doc_id}, metadata: {vertex_metadata}")

            success, message = vertex_ai_importer.create_document_with_id(
                document_id=vertex_doc_id,  # Use blob_name WITHOUT extension
                gcs_uri=doc["gcs_uri"],
                mime_type=doc["content_type"],
                metadata=vertex_metadata,
            )

            if success:
                logger.info(f"✅ Successfully created document in Vertex AI: {vertex_doc_id}")
                import_successes.append(vertex_doc_id)
            else:
                logger.error(f"❌ Failed to create document in Vertex AI: {message}")
                import_failures.append({"document_id": doc["document_id"], "error": message})

        except Exception as e:
            error_msg = f"Failed to create document in Vertex AI: {str(e)}"
            logger.error(f"Error for {doc['document_id']}: {error_msg}")
            import_failures.append({"document_id": doc["document_id"], "error": error_msg})

    import_success = len(import_successes) > 0
    import_operation = (
        f"Created {len(import_successes)} documents with metadata"
        if import_success
        else "Failed to create documents in Vertex AI"
    )

    # Save document metadata to PostgreSQL
    db_saved_documents = []
    for doc in uploaded_documents:
        try:
            # Use blob_name WITHOUT extension as vertex_ai_doc_id (matches Vertex AI)
            vertex_doc_id = Path(doc["document_id"]).stem
            # Replace all invalid characters (periods, spaces, etc.) with underscores
            vertex_doc_id = re.sub(r'[^a-zA-Z0-9_-]', '_', vertex_doc_id)
            doc_id = await db.insert_document(
                user_id=user_id,
                collection_id=collection_id,
                original_filename=doc["original_filename"],
                gcs_blob_name=doc["gcs_blob_name"],
                gcs_uri=doc["gcs_uri"],
                vertex_ai_doc_id=vertex_doc_id,  # Store WITHOUT extension
                file_type=doc["file_type"],
                file_size_bytes=doc["size_bytes"],
                content_type=doc["content_type"],
                import_operation_id=import_operation if import_success else None,
            )
            doc["db_id"] = str(doc_id)
            db_saved_documents.append(doc)
            logger.info(f"Saved document metadata to database: {doc_id}")
        except Exception as e:
            logger.error(f"Failed to save document metadata to database: {str(e)}")
            # Continue - don't fail the entire request

    # Prepare response
    response = {
        "status": "accepted",
        "message": f"Successfully uploaded {len(uploaded_documents)} document(s) to '{collection['name']}' collection",
        "collection_id": str(collection_id),
        "collection_name": collection["name"],
        "documents": uploaded_documents,
        "vertex_ai_import": {
            "triggered": import_success,
            "successes": len(import_successes),
            "failures": len(import_failures),
            "operation_name": import_operation if import_success else None,
            "status_message": (
                f"✅ Created {len(import_successes)} document(s) in Vertex AI Search with collection metadata for filtering"
                if import_success
                else "❌ Import failed - files are in GCS but indexing failed"
            ),
        },
    }

    if import_failures:
        response["vertex_ai_import"]["failed_imports"] = import_failures

    if failed_uploads:
        response["failed_uploads"] = failed_uploads
        response["warning"] = (
            f"{len(failed_uploads)} file(s) failed validation or upload"
        )

    return JSONResponse(content=response, status_code=status.HTTP_202_ACCEPTED)


@app.get("/documents", tags=["Documents"])
async def list_user_documents(
    user_id: str = Query(..., description="User ID to list documents for"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of documents to return"),
    offset: int = Query(0, ge=0, description="Number of documents to skip"),
    status: Optional[str] = Query(None, description="Filter by status (e.g., 'uploaded')"),
):
    """
    List ALL documents for a specific user across all collections (fast PostgreSQL query).

    This endpoint queries PostgreSQL directly for fast results without
    hitting Vertex AI Search API. Documents include collection_name
    to show which collection they belong to.

    Args:
        user_id: User identifier
        limit: Maximum number of documents to return (default 100, max 1000)
        offset: Number of documents to skip for pagination
        status: Optional status filter

    Returns:
        List of user's documents with metadata and collection_name
    """
    try:
        # Get documents from PostgreSQL
        documents = await db.list_documents_by_user(
            user_id=user_id,
            limit=limit,
            offset=offset,
            status=status,
        )

        # Get total count for pagination
        total_count = await db.count_user_documents(user_id=user_id, status=status)

        # Convert datetime objects and UUIDs to strings for JSON serialization
        for doc in documents:
            if doc.get("upload_date"):
                doc["upload_date"] = doc["upload_date"].isoformat()
            if doc.get("created_at"):
                doc["created_at"] = doc["created_at"].isoformat()
            if doc.get("updated_at"):
                doc["updated_at"] = doc["updated_at"].isoformat()
            # Convert UUIDs to strings
            if doc.get("id"):
                doc["id"] = str(doc["id"])
            if doc.get("collection_id"):
                doc["collection_id"] = str(doc["collection_id"])

        return {
            "user_id": user_id,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "returned_count": len(documents),
            "documents": documents,
        }

    except Exception as e:
        logger.error(f"Error listing documents for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}",
        )


@app.get("/debug/vertex-ai-documents", tags=["Debug"])
async def list_vertex_ai_documents(
    page_size: int = Query(100, ge=1, le=1000, description="Number of documents to return"),
):
    """
    DEBUG ENDPOINT: List all documents currently in Vertex AI Search datastore.

    This is useful for debugging document ID mismatches between PostgreSQL
    and Vertex AI Search. It shows the actual document IDs that Vertex AI
    is using, which should match the gcs_blob_name in your database.

    Args:
        page_size: Number of documents to return (max 1000)

    Returns:
        List of documents with their IDs, names, URIs, and metadata
    """
    try:
        documents = vertex_ai_importer.list_documents(page_size=page_size)

        return {
            "status": "success",
            "count": len(documents),
            "documents": documents,
            "note": "Compare the 'id' field here with the 'vertex_ai_doc_id' in your PostgreSQL database. They should match!",
        }

    except Exception as e:
        logger.error(f"Error listing Vertex AI documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list Vertex AI documents: {str(e)}",
        )


@app.get("/debug/verify-document/{vertex_ai_doc_id}", tags=["Debug"])
async def verify_document_in_vertex_ai(
    vertex_ai_doc_id: str,
):
    """
    DEBUG ENDPOINT: Check if a specific document exists in Vertex AI Search.

    Use this to verify that a document has been successfully deleted or
    that it exists after upload.

    Args:
        vertex_ai_doc_id: The document ID to check (should match gcs_blob_name)

    Returns:
        Document existence status and data if it exists
    """
    try:
        exists, doc_data = vertex_ai_importer.get_document(vertex_ai_doc_id)

        if exists:
            return {
                "status": "found",
                "exists": True,
                "message": f"✅ Document exists in Vertex AI Search",
                "document": doc_data,
            }
        else:
            return {
                "status": "not_found",
                "exists": False,
                "message": f"❌ Document does NOT exist in Vertex AI Search (deleted or never indexed)",
                "document_id": vertex_ai_doc_id,
            }

    except Exception as e:
        logger.error(f"Error verifying document in Vertex AI: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify document: {str(e)}",
        )


@app.delete("/documents/{doc_id}", tags=["Documents"])
async def delete_document(
    doc_id: UUID,
    user_id: str = Query(..., description="User ID for ownership verification"),
):
    """
    Delete a document with ownership verification.

    This endpoint:
    1. Verifies ownership via PostgreSQL
    2. Deletes the specific file from GCS (not the entire bucket)
    3. Deletes the document from Vertex AI Search
    4. Deletes the metadata from PostgreSQL

    Args:
        doc_id: Document UUID from PostgreSQL
        user_id: User ID for ownership verification

    Returns:
        Success message with deletion details

    Raises:
        HTTPException: 404 if not found, 403 if unauthorized, 500 on error
    """
    try:
        # Step 1: Get document from PostgreSQL and verify ownership
        document = await db.get_document_by_id(doc_id)

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {doc_id} not found",
            )

        if document["user_id"] != user_id:
            logger.warning(
                f"Unauthorized delete attempt: user {user_id} tried to delete "
                f"document {doc_id} owned by {document['user_id']}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You do not have permission to delete this document",
            )

        # Check if document is still indexing
        index_status = document.get("index_status", "indexed")
        if index_status in ["pending", "indexing"]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot delete document while it is still being indexed. Status: {index_status}. Please wait for indexing to complete.",
            )

        # Step 2: Delete from GCS (specific file, not bucket)
        try:
            gcs_deleted = gcs_uploader.delete_file(document["gcs_blob_name"])
            if gcs_deleted:
                logger.info(f"Deleted file from GCS: {document['gcs_blob_name']}")
        except Exception as e:
            logger.error(f"Failed to delete from GCS: {str(e)}")
            # Continue with deletion - file might already be gone

        # Step 3: Delete from Vertex AI Search using URI (works around ID mismatch)
        vertex_ai_deleted = False
        vertex_ai_verification = None

        try:
            # Use URI-based deletion (reliable method)
            vertex_ai_success, vertex_ai_msg = vertex_ai_importer.delete_document_by_uri(
                gcs_uri=document["gcs_uri"]
            )
            if vertex_ai_success:
                logger.info(f"✅ Deleted from Vertex AI: {document['vertex_ai_doc_id']}")
                vertex_ai_deleted = True

                # Verify deletion by checking if document still exists
                import time
                time.sleep(1)  # Brief wait for deletion to propagate
                verified, verify_msg = vertex_ai_importer.verify_deletion(
                    document["vertex_ai_doc_id"]
                )
                vertex_ai_verification = {
                    "verified": verified,
                    "message": verify_msg
                }
                logger.info(verify_msg)
            else:
                # Failed to delete - add to retry queue
                if "404" in vertex_ai_msg or "does not exist" in vertex_ai_msg.lower():
                    logger.warning(
                        f"⚠️  Document not yet indexed in Vertex AI. Adding to retry queue: "
                        f"{document['vertex_ai_doc_id']}"
                    )
                    await deletion_queue.enqueue_deletion(
                        vertex_ai_doc_id=document["vertex_ai_doc_id"],
                        user_id=user_id,
                        original_filename=document["original_filename"],
                    )
                else:
                    logger.warning(f"Vertex AI deletion warning: {vertex_ai_msg}")
        except Exception as e:
            logger.error(f"Failed to delete from Vertex AI: {str(e)}")
            # Add to retry queue
            await deletion_queue.enqueue_deletion(
                vertex_ai_doc_id=document["vertex_ai_doc_id"],
                user_id=user_id,
                original_filename=document["original_filename"],
            )

        # Step 4: Delete from PostgreSQL
        db_deleted = await db.delete_document(doc_id=doc_id, user_id=user_id)

        if not db_deleted:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete document metadata from database",
            )

        response = {
            "status": "success",
            "message": f"Document {doc_id} deleted successfully",
            "deleted": {
                "document_id": str(doc_id),
                "original_filename": document["original_filename"],
                "gcs_blob_name": document["gcs_blob_name"],
                "vertex_ai_doc_id": document["vertex_ai_doc_id"],
            },
            "deletion_status": {
                "postgresql": True,
                "gcs": gcs_deleted,
                "vertex_ai": vertex_ai_deleted,
            }
        }

        if vertex_ai_verification:
            response["vertex_ai_verification"] = vertex_ai_verification

        return response

    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error deleting document {doc_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}",
        )


@app.get("/deletion-queue/stats", tags=["Admin"])
async def get_deletion_queue_stats():
    """
    Get statistics about the deletion queue.

    Returns counts of pending and failed deletions.
    Useful for monitoring orphaned document cleanup.
    """
    try:
        stats = await deletion_queue.get_queue_stats()
        return {
            "status": "success",
            "queue_stats": stats,
            "message": (
                "Pending deletions will be automatically retried in the background."
            ),
        }
    except Exception as e:
        logger.error(f"Error getting deletion queue stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get deletion queue stats: {str(e)}",
        )


@app.get("/operation/{operation_name:path}", tags=["Documents"])
async def check_operation_status(operation_name: str):
    """
    Check the status of a Vertex AI Search import operation.

    Args:
        operation_name: The operation name returned from the upload endpoint

    Returns:
        Operation status information
    """
    try:
        status_info = vertex_ai_importer.check_operation_status(operation_name)
        return JSONResponse(content=status_info)
    except Exception as e:
        logger.error(f"Error checking operation status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check operation status: {str(e)}",
        )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
