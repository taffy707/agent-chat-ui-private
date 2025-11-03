"""
Database module for PostgreSQL integration.

Manages async connection pool and provides CRUD operations for document metadata.
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

import asyncpg
from asyncpg import Pool

from config import settings

logger = logging.getLogger(__name__)


class Database:
    """Async PostgreSQL database manager using asyncpg connection pool."""

    def __init__(self):
        self.pool: Optional[Pool] = None

    async def connect(self):
        """Initialize database connection pool."""
        try:
            self.pool = await asyncpg.create_pool(
                host=settings.POSTGRES_HOST,
                port=settings.POSTGRES_PORT,
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                database=settings.POSTGRES_DB,
                min_size=2,
                max_size=10,
                command_timeout=60,
            )
            logger.info(
                f"✅ Database connection pool established: "
                f"{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
            )
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {str(e)}")
            raise

    async def disconnect(self):
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")

    async def initialize_schema(self):
        """Create database schema if it doesn't exist."""
        schema_sql = """
        -- Create collections table first (referenced by documents)
        CREATE TABLE IF NOT EXISTS collections (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id VARCHAR(255) NOT NULL,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(user_id, name)
        );

        -- Create indexes for collections
        CREATE INDEX IF NOT EXISTS idx_collections_user_id ON collections(user_id);
        CREATE INDEX IF NOT EXISTS idx_collections_created_at ON collections(created_at DESC);

        -- Create documents table
        CREATE TABLE IF NOT EXISTS documents (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id VARCHAR(255) NOT NULL,
            collection_id UUID NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
            original_filename VARCHAR(500) NOT NULL,
            gcs_blob_name VARCHAR(500) NOT NULL,
            gcs_uri TEXT NOT NULL,
            vertex_ai_doc_id VARCHAR(500) NOT NULL UNIQUE,
            file_type VARCHAR(100) NOT NULL,
            file_size_bytes BIGINT NOT NULL,
            content_type VARCHAR(100) NOT NULL,
            upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            status VARCHAR(50) DEFAULT 'uploaded',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        -- Create indexes for fast queries
        CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
        CREATE INDEX IF NOT EXISTS idx_documents_collection_id ON documents(collection_id);
        CREATE INDEX IF NOT EXISTS idx_documents_upload_date ON documents(upload_date DESC);
        CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
        CREATE INDEX IF NOT EXISTS idx_documents_user_collection ON documents(user_id, collection_id);
        CREATE INDEX IF NOT EXISTS idx_documents_user_id_upload_date ON documents(user_id, upload_date DESC);

        -- Create updated_at trigger
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';

        DROP TRIGGER IF EXISTS update_documents_updated_at ON documents;
        CREATE TRIGGER update_documents_updated_at
            BEFORE UPDATE ON documents
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();

        DROP TRIGGER IF EXISTS update_collections_updated_at ON collections;
        CREATE TRIGGER update_collections_updated_at
            BEFORE UPDATE ON collections
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """

        try:
            async with self.pool.acquire() as conn:
                await conn.execute(schema_sql)
            logger.info("✅ Database schema initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize database schema: {str(e)}")
            raise

    async def insert_document(
        self,
        user_id: str,
        collection_id: UUID,
        original_filename: str,
        gcs_blob_name: str,
        gcs_uri: str,
        vertex_ai_doc_id: str,
        file_type: str,
        file_size_bytes: int,
        content_type: str,
        import_operation_id: Optional[str] = None,
    ) -> UUID:
        """
        Insert a new document record.

        Args:
            user_id: User identifier who uploaded the document
            collection_id: Collection UUID this document belongs to
            original_filename: Original name of the uploaded file
            gcs_blob_name: Blob name in GCS bucket (with UUID prefix)
            gcs_uri: Full GCS URI (gs://bucket/blob)
            vertex_ai_doc_id: Document ID in Vertex AI Search
            file_type: File extension (e.g., .pdf, .txt)
            file_size_bytes: File size in bytes
            content_type: MIME type of the file
            import_operation_id: Vertex AI import operation ID for tracking

        Returns:
            UUID: The generated document ID
        """
        query = """
        INSERT INTO documents (
            user_id, collection_id, original_filename, gcs_blob_name, gcs_uri,
            vertex_ai_doc_id, file_type, file_size_bytes, content_type,
            import_operation_id, index_status
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        RETURNING id
        """

        # Set initial status based on whether we have an operation ID
        index_status = 'indexing' if import_operation_id else 'pending'

        try:
            async with self.pool.acquire() as conn:
                doc_id = await conn.fetchval(
                    query,
                    user_id,
                    collection_id,
                    original_filename,
                    gcs_blob_name,
                    gcs_uri,
                    vertex_ai_doc_id,
                    file_type,
                    file_size_bytes,
                    content_type,
                    import_operation_id,
                    index_status,
                )
            logger.info(f"✅ Document metadata saved to database: {doc_id}")
            return doc_id
        except Exception as e:
            logger.error(f"❌ Failed to insert document: {str(e)}")
            raise

    async def list_documents_by_user(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List documents for a specific user across all collections.

        Args:
            user_id: User identifier
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            status: Optional status filter

        Returns:
            List of document records with collection_name included
        """
        if status:
            query = """
            SELECT d.id, d.user_id, d.collection_id, d.original_filename, d.gcs_blob_name, d.gcs_uri,
                   d.vertex_ai_doc_id, d.file_type, d.file_size_bytes, d.content_type,
                   d.upload_date, d.status, d.created_at, d.updated_at,
                   c.name as collection_name
            FROM documents d
            JOIN collections c ON d.collection_id = c.id
            WHERE d.user_id = $1 AND d.status = $2
            ORDER BY d.upload_date DESC
            LIMIT $3 OFFSET $4
            """
            params = (user_id, status, limit, offset)
        else:
            query = """
            SELECT d.id, d.user_id, d.collection_id, d.original_filename, d.gcs_blob_name, d.gcs_uri,
                   d.vertex_ai_doc_id, d.file_type, d.file_size_bytes, d.content_type,
                   d.upload_date, d.status, d.created_at, d.updated_at,
                   c.name as collection_name
            FROM documents d
            JOIN collections c ON d.collection_id = c.id
            WHERE d.user_id = $1
            ORDER BY d.upload_date DESC
            LIMIT $2 OFFSET $3
            """
            params = (user_id, limit, offset)

        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
            documents = [dict(row) for row in rows]
            logger.info(
                f"Retrieved {len(documents)} documents for user: {user_id}"
            )
            return documents
        except Exception as e:
            logger.error(f"❌ Failed to list documents: {str(e)}")
            raise

    async def count_user_documents(
        self, user_id: str, status: Optional[str] = None
    ) -> int:
        """
        Count total documents for a user.

        Args:
            user_id: User identifier
            status: Optional status filter

        Returns:
            Total count of documents
        """
        if status:
            query = "SELECT COUNT(*) FROM documents WHERE user_id = $1 AND status = $2"
            params = (user_id, status)
        else:
            query = "SELECT COUNT(*) FROM documents WHERE user_id = $1"
            params = (user_id,)

        try:
            async with self.pool.acquire() as conn:
                count = await conn.fetchval(query, *params)
            return count
        except Exception as e:
            logger.error(f"❌ Failed to count documents: {str(e)}")
            raise

    async def get_document_by_id(self, doc_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get a single document by ID.

        Args:
            doc_id: Document UUID

        Returns:
            Document record as dictionary or None if not found
        """
        query = """
        SELECT id, user_id, original_filename, gcs_blob_name, gcs_uri,
               vertex_ai_doc_id, file_type, file_size_bytes, content_type,
               upload_date, status, created_at, updated_at
        FROM documents
        WHERE id = $1
        """

        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, doc_id)
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get document: {str(e)}")
            raise

    async def delete_document(self, doc_id: UUID, user_id: str) -> bool:
        """
        Delete a document (with ownership verification).

        Args:
            doc_id: Document UUID
            user_id: User identifier for ownership verification

        Returns:
            True if deleted, False if not found or unauthorized
        """
        query = """
        DELETE FROM documents
        WHERE id = $1 AND user_id = $2
        RETURNING id
        """

        try:
            async with self.pool.acquire() as conn:
                deleted_id = await conn.fetchval(query, doc_id, user_id)
            if deleted_id:
                logger.info(f"✅ Document deleted from database: {doc_id}")
                return True
            else:
                logger.warning(
                    f"⚠️  Document not found or unauthorized: {doc_id} for user {user_id}"
                )
                return False
        except Exception as e:
            logger.error(f"❌ Failed to delete document: {str(e)}")
            raise

    async def update_document_status(
        self, doc_id: UUID, status: str
    ) -> bool:
        """
        Update document status.

        Args:
            doc_id: Document UUID
            status: New status value

        Returns:
            True if updated, False if not found
        """
        query = """
        UPDATE documents
        SET status = $1
        WHERE id = $2
        RETURNING id
        """

        try:
            async with self.pool.acquire() as conn:
                updated_id = await conn.fetchval(query, status, doc_id)
            if updated_id:
                logger.info(f"✅ Document status updated: {doc_id} -> {status}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to update document status: {str(e)}")
            raise

    # ============================================================
    # Collection Management Methods
    # ============================================================

    async def create_collection(
        self, user_id: str, name: str, description: Optional[str] = None
    ) -> UUID:
        """
        Create a new collection.

        Args:
            user_id: User identifier
            name: Collection name (unique per user)
            description: Optional description

        Returns:
            UUID: The generated collection ID
        """
        query = """
        INSERT INTO collections (user_id, name, description)
        VALUES ($1, $2, $3)
        RETURNING id
        """

        try:
            async with self.pool.acquire() as conn:
                collection_id = await conn.fetchval(query, user_id, name, description)
            logger.info(f"✅ Collection created: {collection_id} - {name}")
            return collection_id
        except Exception as e:
            logger.error(f"❌ Failed to create collection: {str(e)}")
            raise

    async def list_collections(
        self, user_id: str, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List collections for a user with document counts.

        Args:
            user_id: User identifier
            limit: Maximum collections to return
            offset: Number to skip

        Returns:
            List of collection records with document_count
        """
        query = """
        SELECT
            c.id,
            c.user_id,
            c.name,
            c.description,
            c.created_at,
            c.updated_at,
            COUNT(d.id) as document_count
        FROM collections c
        LEFT JOIN documents d ON d.collection_id = c.id
        WHERE c.user_id = $1
        GROUP BY c.id
        ORDER BY c.created_at DESC
        LIMIT $2 OFFSET $3
        """

        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, user_id, limit, offset)
            collections = [dict(row) for row in rows]
            logger.info(f"Retrieved {len(collections)} collections for user: {user_id}")
            return collections
        except Exception as e:
            logger.error(f"❌ Failed to list collections: {str(e)}")
            raise

    async def count_user_collections(self, user_id: str) -> int:
        """Count total collections for a user."""
        query = "SELECT COUNT(*) FROM collections WHERE user_id = $1"
        try:
            async with self.pool.acquire() as conn:
                count = await conn.fetchval(query, user_id)
            return count
        except Exception as e:
            logger.error(f"❌ Failed to count collections: {str(e)}")
            raise

    async def get_collection_by_id(
        self, collection_id: UUID, user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get collection by ID with document count.

        Args:
            collection_id: Collection UUID
            user_id: Optional user_id for ownership verification

        Returns:
            Collection record or None if not found
        """
        if user_id:
            query = """
            SELECT
                c.id,
                c.user_id,
                c.name,
                c.description,
                c.created_at,
                c.updated_at,
                COUNT(d.id) as document_count
            FROM collections c
            LEFT JOIN documents d ON d.collection_id = c.id
            WHERE c.id = $1 AND c.user_id = $2
            GROUP BY c.id
            """
            params = (collection_id, user_id)
        else:
            query = """
            SELECT
                c.id,
                c.user_id,
                c.name,
                c.description,
                c.created_at,
                c.updated_at,
                COUNT(d.id) as document_count
            FROM collections c
            LEFT JOIN documents d ON d.collection_id = c.id
            WHERE c.id = $1
            GROUP BY c.id
            """
            params = (collection_id,)

        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, *params)
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get collection: {str(e)}")
            raise

    async def update_collection(
        self,
        collection_id: UUID,
        user_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> bool:
        """
        Update collection name or description.

        Args:
            collection_id: Collection UUID
            user_id: User ID for ownership verification
            name: New name (optional)
            description: New description (optional)

        Returns:
            True if updated, False if not found
        """
        # Build dynamic update query
        updates = []
        params = []
        param_count = 1

        if name is not None:
            updates.append(f"name = ${param_count}")
            params.append(name)
            param_count += 1

        if description is not None:
            updates.append(f"description = ${param_count}")
            params.append(description)
            param_count += 1

        if not updates:
            return False

        query = f"""
        UPDATE collections
        SET {', '.join(updates)}
        WHERE id = ${param_count} AND user_id = ${param_count + 1}
        RETURNING id
        """
        params.extend([collection_id, user_id])

        try:
            async with self.pool.acquire() as conn:
                updated_id = await conn.fetchval(query, *params)
            if updated_id:
                logger.info(f"✅ Collection updated: {collection_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to update collection: {str(e)}")
            raise

    async def delete_collection(
        self, collection_id: UUID, user_id: str
    ) -> tuple[bool, int]:
        """
        Delete a collection (CASCADE deletes all documents).

        Args:
            collection_id: Collection UUID
            user_id: User ID for ownership verification

        Returns:
            Tuple of (success: bool, documents_deleted: int)
        """
        # First count documents
        count_query = """
        SELECT COUNT(*) FROM documents
        WHERE collection_id = $1
        """

        # Delete collection (CASCADE will delete documents)
        delete_query = """
        DELETE FROM collections
        WHERE id = $1 AND user_id = $2
        RETURNING id
        """

        try:
            async with self.pool.acquire() as conn:
                # Count documents first
                doc_count = await conn.fetchval(count_query, collection_id)

                # Delete collection
                deleted_id = await conn.fetchval(delete_query, collection_id, user_id)

            if deleted_id:
                logger.info(
                    f"✅ Collection deleted: {collection_id} ({doc_count} documents)"
                )
                return True, doc_count
            else:
                logger.warning(
                    f"⚠️  Collection not found or unauthorized: {collection_id} for user {user_id}"
                )
                return False, 0
        except Exception as e:
            logger.error(f"❌ Failed to delete collection: {str(e)}")
            raise

    async def list_documents_by_collection(
        self,
        collection_id: UUID,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        List documents in a specific collection.

        Args:
            collection_id: Collection UUID
            user_id: User ID for ownership verification
            limit: Maximum documents to return
            offset: Number to skip

        Returns:
            List of document records
        """
        query = """
        SELECT id, user_id, collection_id, original_filename, gcs_blob_name, gcs_uri,
               vertex_ai_doc_id, file_type, file_size_bytes, content_type,
               upload_date, status, created_at, updated_at
        FROM documents
        WHERE collection_id = $1 AND user_id = $2
        ORDER BY upload_date DESC
        LIMIT $3 OFFSET $4
        """

        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, collection_id, user_id, limit, offset)
            documents = [dict(row) for row in rows]
            logger.info(
                f"Retrieved {len(documents)} documents for collection: {collection_id}"
            )
            return documents
        except Exception as e:
            logger.error(f"❌ Failed to list documents by collection: {str(e)}")
            raise

    async def count_collection_documents(
        self, collection_id: UUID, user_id: str
    ) -> int:
        """Count documents in a collection."""
        query = "SELECT COUNT(*) FROM documents WHERE collection_id = $1 AND user_id = $2"
        try:
            async with self.pool.acquire() as conn:
                count = await conn.fetchval(query, collection_id, user_id)
            return count
        except Exception as e:
            logger.error(f"❌ Failed to count collection documents: {str(e)}")
            raise

    async def update_document_index_status(
        self,
        document_id: UUID,
        index_status: str,
        index_completed_at: Optional[datetime] = None,
    ) -> bool:
        """
        Update the indexing status of a document.

        Args:
            document_id: Document UUID
            index_status: New status (pending, indexing, indexed, failed)
            index_completed_at: Timestamp when indexing completed (optional)

        Returns:
            bool: True if update successful
        """
        if index_completed_at:
            query = """
            UPDATE documents
            SET index_status = $1,
                index_completed_at = $2,
                updated_at = NOW()
            WHERE id = $3
            """
            params = (index_status, index_completed_at, document_id)
        else:
            query = """
            UPDATE documents
            SET index_status = $1,
                updated_at = NOW()
            WHERE id = $2
            """
            params = (index_status, document_id)

        try:
            async with self.pool.acquire() as conn:
                await conn.execute(query, *params)
            logger.info(f"✅ Updated document {document_id} index_status to '{index_status}'")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to update document index status: {str(e)}")
            return False

    async def get_documents_by_index_status(
        self, index_status: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get documents by index status.

        Args:
            index_status: Status to filter by (pending, indexing, indexed, failed)
            limit: Maximum number of documents to return

        Returns:
            List of document records
        """
        query = """
        SELECT id, user_id, collection_id, vertex_ai_doc_id,
               import_operation_id, index_status, index_completed_at,
               original_filename, upload_date
        FROM documents
        WHERE index_status = $1
        ORDER BY upload_date DESC
        LIMIT $2
        """

        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, index_status, limit)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"❌ Failed to get documents by index status: {str(e)}")
            raise


# Global database instance
db = Database()
