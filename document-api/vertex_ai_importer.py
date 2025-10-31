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

    def import_documents_from_gcs(
        self, gcs_uris: list[str], reconciliation_mode: str = "INCREMENTAL"
    ) -> tuple[bool, str]:
        """
        Import documents from GCS into Vertex AI Search.

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

    def delete_document(self, vertex_ai_doc_id: str) -> tuple[bool, str]:
        """
        Delete a specific document from Vertex AI Search.

        Args:
            vertex_ai_doc_id: The document ID in Vertex AI Search (same as GCS blob name)

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

            # Create delete request
            request = discoveryengine.DeleteDocumentRequest(
                name=document_name,
            )

            # Delete the document
            self.client.delete_document(request=request)

            logger.info(f"Successfully deleted document from Vertex AI: {vertex_ai_doc_id}")
            return True, f"Document {vertex_ai_doc_id} deleted from Vertex AI Search"

        except GoogleAPIError as e:
            logger.error(f"Failed to delete document from Vertex AI: {str(e)}")
            return False, str(e)
