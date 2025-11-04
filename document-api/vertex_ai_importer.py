"""
Vertex AI Search document importer.

Triggers import of documents from GCS into Vertex AI Search datastore.
Based on patterns from create_datastore_and_search.ipynb and
ingesting_unstructured_documents_with_metadata.ipynb
"""

import logging
from typing import Optional

from google.api_core.client_options import ClientOptions
from google.cloud import discoveryengine_v1alpha as discoveryengine
from google.api_core.exceptions import GoogleAPIError

logger = logging.getLogger(__name__)


class VertexAIImporter:
    """Handles importing documents into Vertex AI Search."""

    def __init__(self, project_id: str, location: str, data_store_id: str):
        """
        Initialize Vertex AI Search importer.

        Args:
            project_id: Google Cloud project ID
            location: Datastore location (global, us, eu)
            data_store_id: Vertex AI Search datastore ID
        """
        self.project_id = project_id
        self.location = location
        self.data_store_id = data_store_id

        # Create client with location-specific endpoint
        client_options = (
            ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")
            if location != "global"
            else None
        )
        self.client = discoveryengine.DocumentServiceClient(
            client_options=client_options
        )

    def create_document_with_id(
        self, document_id: str, gcs_uri: str, mime_type: str = None, metadata: dict = None
    ) -> tuple[bool, str]:
        """
        Create a document in Vertex AI Search with an explicit document ID.

        This approach ensures that the document ID in Vertex AI matches
        the ID we store in our database, making deletion reliable.

        Args:
            document_id: Custom document ID (e.g., blob name like "uuid_filename.pdf")
            gcs_uri: GCS URI where the document is stored
            mime_type: MIME type of the document (e.g., "application/pdf")
            metadata: Optional metadata dictionary for filtering/search (e.g., collection info)

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Construct the parent path for the branch
            parent = self.client.branch_path(
                project=self.project_id,
                location=self.location,
                data_store=self.data_store_id,
                branch="default_branch",
            )

            # Create document content
            content = discoveryengine.Document.Content(
                uri=gcs_uri,
            )

            # Set MIME type if provided (Vertex AI can auto-detect from file extension)
            if mime_type:
                content.mime_type = mime_type

            # Create document object with explicit ID
            document = discoveryengine.Document(
                id=document_id,
                content=content,
            )

            # Add metadata if provided (for collection filtering and search)
            if metadata:
                from google.protobuf.struct_pb2 import Struct
                struct_data = Struct()
                struct_data.update(metadata)
                document.struct_data = struct_data

            # Create the document
            request = discoveryengine.CreateDocumentRequest(
                parent=parent,
                document=document,
                document_id=document_id,
            )

            created_doc = self.client.create_document(request=request)

            logger.info(
                f"Successfully created document in Vertex AI with ID: {document_id}"
            )
            logger.info(
                f"Document will be processed, chunked, embedded, and indexed automatically"
            )

            return True, f"Document {document_id} created in Vertex AI Search"

        except GoogleAPIError as e:
            error_msg = str(e)
            logger.error(f"Failed to create document in Vertex AI: {error_msg}")
            logger.error(f"Document ID: {document_id}, GCS URI: {gcs_uri}")
            return False, error_msg

    def import_documents_from_gcs(
        self, gcs_uris: list[str], reconciliation_mode: str = "INCREMENTAL"
    ) -> tuple[bool, str]:
        """
        Import documents from GCS into Vertex AI Search.

        WARNING: This method allows Vertex AI to auto-generate document IDs,
        which makes deletion unreliable. Use create_document_with_id() instead
        for reliable deletion support.

        This triggers Vertex AI Search to:
        1. Read files from GCS
        2. Extract text from PDF/DOCX/HTML
        3. Chunk documents optimally
        4. Generate embeddings
        5. Index for search

        Args:
            gcs_uris: List of GCS URIs (gs://bucket/path) to import
            reconciliation_mode: INCREMENTAL or FULL
                - INCREMENTAL: Add new docs, update existing
                - FULL: Replace all docs in datastore

        Returns:
            Tuple of (success: bool, operation_name: str)
        """
        try:
            # Construct the parent path for the branch
            parent = self.client.branch_path(
                project=self.project_id,
                location=self.location,
                data_store=self.data_store_id,
                branch="default_branch",
            )

            # Map reconciliation mode string to enum
            mode_mapping = {
                "INCREMENTAL": discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL,
                "FULL": discoveryengine.ImportDocumentsRequest.ReconciliationMode.FULL,
            }
            reconciliation_enum = mode_mapping.get(
                reconciliation_mode,
                discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL,
            )

            # Create import request with GcsSource
            request = discoveryengine.ImportDocumentsRequest(
                parent=parent,
                gcs_source=discoveryengine.GcsSource(
                    input_uris=gcs_uris,
                    data_schema="content",  # Let Vertex AI auto-detect schema
                ),
                reconciliation_mode=reconciliation_enum,
            )

            # Trigger the import operation (async)
            operation = self.client.import_documents(request=request)

            logger.info(
                f"Import operation started: {operation.operation.name} for {len(gcs_uris)} document(s)"
            )
            logger.info(
                "Vertex AI Search will now process, chunk, embed, and index the documents automatically"
            )

            return True, operation.operation.name

        except GoogleAPIError as e:
            logger.error(f"Failed to trigger import: {str(e)}")
            return False, str(e)

    def check_operation_status(self, operation_name: str) -> dict:
        """
        Check the status of a long-running import operation.

        Args:
            operation_name: The operation name returned from import_documents_from_gcs

        Returns:
            Dictionary with operation status information
        """
        try:
            # Get operation status
            from google.api_core import operations_v1

            operations_client = operations_v1.OperationsClient(
                self.client._transport._grpc_channel
            )
            operation = operations_client.get_operation(name=operation_name)

            status = {
                "done": operation.done,
                "name": operation_name,
            }

            if operation.done:
                if operation.HasField("error"):
                    status["error"] = operation.error.message
                    status["success"] = False
                else:
                    status["success"] = True
                    # Parse metadata if available
                    if operation.HasField("metadata"):
                        metadata = discoveryengine.ImportDocumentsMetadata()
                        operation.metadata.Unpack(metadata)
                        status["create_time"] = str(metadata.create_time)
                        status["update_time"] = str(metadata.update_time)

            return status

        except GoogleAPIError as e:
            logger.error(f"Failed to check operation status: {str(e)}")
            return {"error": str(e), "success": False}

    def list_documents(self, page_size: int = 100) -> list[dict]:
        """
        List all documents in the Vertex AI Search datastore.

        Args:
            page_size: Number of documents to return per page

        Returns:
            List of document dictionaries with id, name, and content info
        """
        try:
            # Construct the parent path for the branch
            parent = self.client.branch_path(
                project=self.project_id,
                location=self.location,
                data_store=self.data_store_id,
                branch="default_branch",
            )

            # Create list request
            request = discoveryengine.ListDocumentsRequest(
                parent=parent,
                page_size=page_size,
            )

            # List documents
            page_result = self.client.list_documents(request=request)

            documents = []
            for document in page_result:
                doc_info = {
                    "name": document.name,
                    "id": document.id,
                }

                # Extract GCS URI if available
                if hasattr(document, 'content') and hasattr(document.content, 'uri'):
                    doc_info["gcs_uri"] = document.content.uri

                # Extract struct data (metadata) if available
                if hasattr(document, 'struct_data') and document.struct_data:
                    doc_info["metadata"] = dict(document.struct_data)

                documents.append(doc_info)

            logger.info(f"Listed {len(documents)} documents from Vertex AI Search")
            return documents

        except GoogleAPIError as e:
            logger.error(f"Failed to list documents from Vertex AI: {str(e)}")
            return []

    def get_document(self, vertex_ai_doc_id: str) -> tuple[bool, dict | None]:
        """
        Get a specific document from Vertex AI Search to verify it exists.

        Args:
            vertex_ai_doc_id: The document ID in Vertex AI Search

        Returns:
            Tuple of (exists: bool, document_data: dict | None)
        """
        try:
            # Construct the document path
            document_name = self.client.document_path(
                project=self.project_id,
                location=self.location,
                data_store=self.data_store_id,
                branch="default_branch",
                document=vertex_ai_doc_id,
            )

            # Create get request
            request = discoveryengine.GetDocumentRequest(
                name=document_name,
            )

            # Get the document
            document = self.client.get_document(request=request)

            doc_data = {
                "id": document.id,
                "name": document.name,
            }

            # Extract URI if available
            if hasattr(document, 'content') and hasattr(document.content, 'uri'):
                doc_data["uri"] = document.content.uri

            # Extract metadata if available
            if hasattr(document, 'struct_data') and document.struct_data:
                doc_data["metadata"] = dict(document.struct_data)

            logger.info(f"Document exists in Vertex AI: {vertex_ai_doc_id}")
            return True, doc_data

        except GoogleAPIError as e:
            error_msg = str(e)
            if "404" in error_msg or "not found" in error_msg.lower():
                logger.info(f"Document not found in Vertex AI: {vertex_ai_doc_id}")
                return False, None
            else:
                logger.error(f"Error checking document in Vertex AI: {error_msg}")
                return False, None

    def delete_document_by_uri(self, gcs_uri: str) -> tuple[bool, str]:
        """
        Delete a document from Vertex AI Search by its GCS URI.

        This is the RELIABLE method that works around ID mismatches by:
        1. Listing all documents
        2. Finding the one with matching URI
        3. Deleting by its actual hash ID

        This is necessary because Vertex AI auto-generates hash IDs that don't match our blob names.

        Args:
            gcs_uri: The GCS URI (e.g., gs://bucket/blob_name.pdf)

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Step 1: List all documents to find the one with matching URI
            logger.info(f"Searching for document with URI: {gcs_uri}")
            all_docs = self.list_documents(page_size=1000)

            # Step 2: Find document with matching URI
            matching_doc = None
            for doc in all_docs:
                if doc.get('gcs_uri') == gcs_uri:
                    matching_doc = doc
                    break

            if not matching_doc:
                logger.warning(f"Document not found in Vertex AI with URI: {gcs_uri}")
                # Return success if not found (already deleted or never indexed)
                return True, f"Document not found (may be already deleted or not yet indexed)"

            # Step 3: Delete by actual hash ID
            actual_id = matching_doc['id']
            logger.info(f"Found document - URI: {gcs_uri}, Vertex AI ID: {actual_id}")

            # Call delete_document with the actual hash ID
            success, message = self.delete_document(actual_id)

            if success:
                logger.info(f"✅ Successfully deleted document by URI: {gcs_uri}")
                return True, f"Document deleted (Vertex AI ID: {actual_id})"
            else:
                return False, message

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to delete document by URI: {error_msg}")
            return False, error_msg

    def delete_document(self, vertex_ai_doc_id: str) -> tuple[bool, str]:
        """
        Delete a specific document from Vertex AI Search by its document ID.

        NOTE: Due to ID mismatches, prefer using delete_document_by_uri() instead.

        Args:
            vertex_ai_doc_id: The document ID in Vertex AI Search (hash ID)

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Construct the document path
            document_name = self.client.document_path(
                project=self.project_id,
                location=self.location,
                data_store=self.data_store_id,
                branch="default_branch",
                document=vertex_ai_doc_id,
            )

            logger.info(f"Attempting to delete document with path: {document_name}")

            # Create delete request
            request = discoveryengine.DeleteDocumentRequest(
                name=document_name,
            )

            # Delete the document
            self.client.delete_document(request=request)

            logger.info(f"Successfully deleted document from Vertex AI: {vertex_ai_doc_id}")
            return True, f"Document {vertex_ai_doc_id} deleted from Vertex AI Search"

        except GoogleAPIError as e:
            error_msg = str(e)
            logger.error(f"Failed to delete document from Vertex AI: {error_msg}")
            logger.error(f"Document ID attempted: {vertex_ai_doc_id}")
            return False, error_msg

    def verify_deletion(self, vertex_ai_doc_id: str) -> tuple[bool, str]:
        """
        Verify that a document has been successfully deleted from Vertex AI Search.

        Args:
            vertex_ai_doc_id: The document ID to verify

        Returns:
            Tuple of (deleted: bool, message: str)
        """
        exists, doc_data = self.get_document(vertex_ai_doc_id)

        if exists:
            return False, f"❌ Document still exists in Vertex AI: {vertex_ai_doc_id}"
        else:
            return True, f"✅ Document successfully deleted from Vertex AI: {vertex_ai_doc_id}"
