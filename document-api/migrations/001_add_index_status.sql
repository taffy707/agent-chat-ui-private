-- Migration: Add index status tracking to documents table
-- Date: 2025-11-03
-- Purpose: Track Vertex AI indexing status to prevent deletion race conditions

-- Add index_status column
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS index_status VARCHAR(50) DEFAULT 'pending';

-- Add import_operation_id column to track Vertex AI import operations
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS import_operation_id TEXT;

-- Add index_completed_at timestamp
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS index_completed_at TIMESTAMP WITH TIME ZONE;

-- Create index for querying by index_status
CREATE INDEX IF NOT EXISTS idx_documents_index_status
ON documents(index_status);

-- Create index for finding documents that need status updates
CREATE INDEX IF NOT EXISTS idx_documents_pending_indexing
ON documents(index_status, import_operation_id)
WHERE index_status IN ('pending', 'indexing');

-- Update existing documents to 'indexed' status (assume they're already indexed)
UPDATE documents
SET index_status = 'indexed',
    index_completed_at = upload_date
WHERE index_status = 'pending';

-- Add comment
COMMENT ON COLUMN documents.index_status IS
'Status of Vertex AI indexing: pending, indexing, indexed, failed';

COMMENT ON COLUMN documents.import_operation_id IS
'Vertex AI import operation ID for tracking indexing progress';

COMMENT ON COLUMN documents.index_completed_at IS
'Timestamp when Vertex AI indexing completed successfully';
