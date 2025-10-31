-- Database schema for document metadata storage
-- This schema is automatically applied by database.py on startup
-- You can also run this manually: psql -U postgres -d your_db -f init_db.sql

-- Create documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
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
CREATE INDEX IF NOT EXISTS idx_documents_upload_date ON documents(upload_date DESC);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_user_id_upload_date ON documents(user_id, upload_date DESC);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for automatic updated_at updates
DROP TRIGGER IF EXISTS update_documents_updated_at ON documents;
CREATE TRIGGER update_documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Sample queries for testing

-- List all documents for a user
-- SELECT * FROM documents WHERE user_id = 'alice' ORDER BY upload_date DESC;

-- Count documents by user
-- SELECT user_id, COUNT(*) as doc_count FROM documents GROUP BY user_id;

-- Get document by ID
-- SELECT * FROM documents WHERE id = 'your-uuid-here';

-- Delete document (with ownership verification)
-- DELETE FROM documents WHERE id = 'your-uuid-here' AND user_id = 'alice';

-- Update document status
-- UPDATE documents SET status = 'indexed' WHERE id = 'your-uuid-here';
