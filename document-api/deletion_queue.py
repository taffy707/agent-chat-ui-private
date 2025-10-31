"""
Background deletion queue with retry logic.

Handles cases where Vertex AI deletion fails because document isn't indexed yet.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID

import asyncpg

from config import settings
from vertex_ai_importer import VertexAIImporter

logger = logging.getLogger(__name__)


class DeletionQueue:
    """Manages pending deletions with retry logic."""

    def __init__(self, db_pool: asyncpg.Pool, vertex_ai_importer: VertexAIImporter):
        self.db_pool = db_pool
        self.vertex_ai_importer = vertex_ai_importer
        self.running = False

    async def initialize_schema(self):
        """Create deletion queue table if it doesn't exist."""
        schema_sql = """
        CREATE TABLE IF NOT EXISTS deletion_queue (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            vertex_ai_doc_id VARCHAR(500) NOT NULL,
            user_id VARCHAR(255) NOT NULL,
            original_filename VARCHAR(500),
            attempt_count INT DEFAULT 0,
            max_attempts INT DEFAULT 10,
            next_retry_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            last_error TEXT,
            status VARCHAR(50) DEFAULT 'pending'
        );

        CREATE INDEX IF NOT EXISTS idx_deletion_queue_status_retry
        ON deletion_queue(status, next_retry_at)
        WHERE status = 'pending';
        """

        async with self.db_pool.acquire() as conn:
            await conn.execute(schema_sql)
        logger.info("✅ Deletion queue schema initialized")

    async def enqueue_deletion(
        self,
        vertex_ai_doc_id: str,
        user_id: str,
        original_filename: Optional[str] = None,
    ) -> UUID:
        """
        Add a document to the deletion queue for retry.

        Args:
            vertex_ai_doc_id: Document ID in Vertex AI
            user_id: User who requested deletion
            original_filename: Optional filename for logging

        Returns:
            Queue entry ID
        """
        query = """
        INSERT INTO deletion_queue (vertex_ai_doc_id, user_id, original_filename)
        VALUES ($1, $2, $3)
        RETURNING id
        """

        async with self.db_pool.acquire() as conn:
            queue_id = await conn.fetchval(
                query, vertex_ai_doc_id, user_id, original_filename
            )

        logger.info(
            f"📝 Enqueued deletion for Vertex AI doc: {vertex_ai_doc_id} (queue_id: {queue_id})"
        )
        return queue_id

    async def process_pending_deletions(self) -> Dict[str, int]:
        """
        Process all pending deletions that are ready for retry.

        Returns:
            Dictionary with counts: {succeeded, failed, skipped}
        """
        # Get pending deletions ready for retry
        query = """
        SELECT id, vertex_ai_doc_id, user_id, original_filename,
               attempt_count, max_attempts, last_error
        FROM deletion_queue
        WHERE status = 'pending'
          AND next_retry_at <= NOW()
        ORDER BY next_retry_at
        LIMIT 100
        """

        async with self.db_pool.acquire() as conn:
            pending = await conn.fetch(query)

        succeeded = 0
        failed = 0
        skipped = 0

        for record in pending:
            result = await self._attempt_deletion(dict(record))
            if result == "succeeded":
                succeeded += 1
            elif result == "failed":
                failed += 1
            else:
                skipped += 1

        if succeeded > 0 or failed > 0:
            logger.info(
                f"🔄 Deletion queue processed: {succeeded} succeeded, "
                f"{failed} failed, {skipped} skipped"
            )

        return {"succeeded": succeeded, "failed": failed, "skipped": skipped}

    async def _attempt_deletion(self, record: Dict[str, Any]) -> str:
        """
        Attempt to delete a single document from Vertex AI.

        Args:
            record: Deletion queue record

        Returns:
            "succeeded", "failed", or "skipped"
        """
        vertex_ai_doc_id = record["vertex_ai_doc_id"]
        attempt_count = record["attempt_count"] + 1
        max_attempts = record["max_attempts"]

        try:
            # Attempt deletion
            success, message = self.vertex_ai_importer.delete_document(
                vertex_ai_doc_id
            )

            if success:
                # Mark as completed and remove from queue
                await self._mark_completed(record["id"])
                logger.info(
                    f"✅ Successfully deleted from Vertex AI: {vertex_ai_doc_id} "
                    f"(attempt {attempt_count})"
                )
                return "succeeded"
            else:
                # Check if it's a 404 (not found)
                if "404" in message or "does not exist" in message.lower():
                    if attempt_count >= max_attempts:
                        # Max retries reached, mark as failed
                        await self._mark_failed(
                            record["id"],
                            attempt_count,
                            f"Max retries reached. Document never appeared in Vertex AI.",
                        )
                        logger.warning(
                            f"⚠️  Gave up on deletion: {vertex_ai_doc_id} "
                            f"(not indexed after {max_attempts} attempts)"
                        )
                        return "failed"
                    else:
                        # Retry with exponential backoff
                        await self._schedule_retry(
                            record["id"], attempt_count, message
                        )
                        logger.debug(
                            f"🔄 Scheduled retry for: {vertex_ai_doc_id} "
                            f"(attempt {attempt_count}/{max_attempts})"
                        )
                        return "skipped"
                else:
                    # Other error, retry
                    await self._schedule_retry(record["id"], attempt_count, message)
                    return "skipped"

        except Exception as e:
            error_msg = str(e)
            if attempt_count >= max_attempts:
                await self._mark_failed(record["id"], attempt_count, error_msg)
                logger.error(
                    f"❌ Failed to delete after {max_attempts} attempts: "
                    f"{vertex_ai_doc_id} - {error_msg}"
                )
                return "failed"
            else:
                await self._schedule_retry(record["id"], attempt_count, error_msg)
                return "skipped"

    async def _schedule_retry(
        self, queue_id: UUID, attempt_count: int, error_msg: str
    ):
        """Schedule next retry with exponential backoff optimized for Vertex AI indexing."""
        # Vertex AI indexing typically takes 2-10 minutes
        # Retry schedule: 2m, 3m, 5m, 10m, 15m, 30m, 1h, 2h, 4h, 8h
        if attempt_count == 1:
            delay_seconds = 120  # 2 minutes
        elif attempt_count == 2:
            delay_seconds = 180  # 3 minutes (total: 5 min)
        elif attempt_count == 3:
            delay_seconds = 300  # 5 minutes (total: 10 min)
        elif attempt_count == 4:
            delay_seconds = 600  # 10 minutes (total: 20 min)
        else:
            # Exponential backoff for later attempts
            delay_seconds = min(900 * (2 ** (attempt_count - 5)), 28800)  # Max 8 hours

        query = """
        UPDATE deletion_queue
        SET attempt_count = $1,
            next_retry_at = NOW() + INTERVAL '1 second' * $2,
            last_error = $3
        WHERE id = $4
        """

        async with self.db_pool.acquire() as conn:
            await conn.execute(query, attempt_count, delay_seconds, error_msg, queue_id)

    async def _mark_completed(self, queue_id: UUID):
        """Mark deletion as completed and remove from queue."""
        query = "DELETE FROM deletion_queue WHERE id = $1"
        async with self.db_pool.acquire() as conn:
            await conn.execute(query, queue_id)

    async def _mark_failed(self, queue_id: UUID, attempt_count: int, error_msg: str):
        """Mark deletion as permanently failed."""
        query = """
        UPDATE deletion_queue
        SET status = 'failed',
            attempt_count = $1,
            last_error = $2
        WHERE id = $3
        """

        async with self.db_pool.acquire() as conn:
            await conn.execute(query, attempt_count, error_msg, queue_id)

    async def start_background_worker(self, interval_seconds: int = 60):
        """
        Start background worker to process deletion queue.

        Args:
            interval_seconds: How often to check for pending deletions
        """
        self.running = True
        logger.info(
            f"🚀 Deletion queue worker started (checking every {interval_seconds}s)"
        )

        while self.running:
            try:
                await self.process_pending_deletions()
            except Exception as e:
                logger.error(f"Error in deletion queue worker: {e}")

            await asyncio.sleep(interval_seconds)

    async def stop_background_worker(self):
        """Stop the background worker."""
        self.running = False
        logger.info("🛑 Deletion queue worker stopped")

    async def get_queue_stats(self) -> Dict[str, int]:
        """Get statistics about the deletion queue."""
        query = """
        SELECT
            COUNT(*) FILTER (WHERE status = 'pending') as pending_count,
            COUNT(*) FILTER (WHERE status = 'failed') as failed_count,
            COUNT(*) as total_count
        FROM deletion_queue
        """

        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(query)

        return {
            "pending": row["pending_count"],
            "failed": row["failed_count"],
            "total": row["total_count"],
        }
