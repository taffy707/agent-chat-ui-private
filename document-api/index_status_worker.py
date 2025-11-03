"""
Background worker to poll Vertex AI import operations and update document index status.

This prevents the deletion race condition where documents are deleted before indexing completes.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

import asyncpg

from database import db
from vertex_ai_importer import VertexAIImporter

logger = logging.getLogger(__name__)


class IndexStatusWorker:
    """Monitors Vertex AI import operations and updates document statuses."""

    def __init__(self, vertex_ai_importer: VertexAIImporter):
        self.vertex_ai_importer = vertex_ai_importer
        self.running = False

    async def check_operation_status(self, operation_name: str) -> str:
        """
        Check the status of a Vertex AI import operation.

        Args:
            operation_name: Full operation name/ID

        Returns:
            Status: 'indexing', 'indexed', or 'failed'
        """
        try:
            # Use the Vertex AI client to check operation status
            from google.api_core import operations_v1
            from google.cloud import discoveryengine_v1

            client = discoveryengine_v1.DocumentServiceClient()
            operations_client = operations_v1.OperationsClient(client.transport.operations_client)

            try:
                operation = operations_client.get_operation(name=operation_name)

                if operation.done:
                    if operation.error and operation.error.message:
                        logger.error(f"Operation {operation_name} failed: {operation.error.message}")
                        return "failed"
                    else:
                        logger.info(f"Operation {operation_name} completed successfully")
                        return "indexed"
                else:
                    return "indexing"
            except Exception as e:
                # If operation not found, it might have completed long ago
                if "404" in str(e) or "not found" in str(e).lower():
                    logger.warning(f"Operation {operation_name} not found, assuming completed")
                    return "indexed"
                raise

        except Exception as e:
            logger.error(f"Error checking operation status: {e}")
            # On error, keep it as indexing - will retry next time
            return "indexing"

    async def process_indexing_documents(self) -> Dict[str, int]:
        """
        Check status of all documents currently indexing.

        Returns:
            Dictionary with counts: {completed, failed, still_indexing}
        """
        # Get documents with status 'indexing' that have an operation ID
        documents = await db.get_documents_by_index_status("indexing")

        completed = 0
        failed = 0
        still_indexing = 0

        for doc in documents:
            import_operation_id = doc.get("import_operation_id")

            if not import_operation_id:
                # No operation ID - can't track, assume indexed after 10 minutes
                upload_time = doc.get("upload_date")
                if upload_time and (datetime.now(upload_time.tzinfo) - upload_time).total_seconds() > 600:
                    logger.warning(
                        f"Document {doc['id']} has no operation ID and is >10min old, marking as indexed"
                    )
                    await db.update_document_index_status(
                        doc["id"], "indexed", datetime.now()
                    )
                    completed += 1
                continue

            # Check operation status
            status = await self.check_operation_status(import_operation_id)

            if status == "indexed":
                # Update document status to indexed
                await db.update_document_index_status(
                    doc["id"], "indexed", datetime.now()
                )
                logger.info(f"✅ Document {doc['id']} ({doc['original_filename']}) is now indexed")
                completed += 1

            elif status == "failed":
                # Update document status to failed
                await db.update_document_index_status(doc["id"], "failed")
                logger.error(f"❌ Document {doc['id']} ({doc['original_filename']}) indexing failed")
                failed += 1

            else:
                # Still indexing
                still_indexing += 1

        if completed > 0 or failed > 0:
            logger.info(
                f"📊 Index status update: {completed} completed, "
                f"{failed} failed, {still_indexing} still indexing"
            )

        return {"completed": completed, "failed": failed, "still_indexing": still_indexing}

    async def start_background_worker(self, interval_seconds: int = 120):
        """
        Start background worker to check indexing status.

        Args:
            interval_seconds: How often to check (default: 2 minutes)
        """
        self.running = True
        logger.info(
            f"🚀 Index status worker started (checking every {interval_seconds}s)"
        )

        while self.running:
            try:
                await self.process_indexing_documents()
            except Exception as e:
                logger.error(f"Error in index status worker: {e}")

            await asyncio.sleep(interval_seconds)

    async def stop_background_worker(self):
        """Stop the background worker."""
        self.running = False
        logger.info("🛑 Index status worker stopped")
