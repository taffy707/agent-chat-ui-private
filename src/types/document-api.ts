// TypeScript types for Document Upload API

export interface Collection {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  document_count: number;
  created_at: string;
  updated_at: string;
}

export type IndexStatus = "pending" | "indexing" | "indexed" | "failed";

export interface Document {
  id: string;
  user_id: string;
  collection_id: string;
  collection_name?: string;
  original_filename: string;
  gcs_blob_name: string;
  gcs_uri: string;
  vertex_ai_doc_id: string;
  file_type: string;
  file_size_bytes: number;
  content_type: string;
  upload_date: string;
  status: string;
  index_status: IndexStatus;
  import_operation_id?: string | null;
  index_completed_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CollectionListResponse {
  user_id: string;
  collections: Collection[];
  total_count: number;
  limit: number;
  offset: number;
}

export interface DocumentListResponse {
  user_id: string;
  documents: Document[];
  total_count: number;
  limit: number;
  offset: number;
}

export interface UploadResponse {
  status: string;
  message: string;
  collection_id: string;
  collection_name: string;
  documents: Array<{
    original_filename: string;
    document_id: string;
    gcs_uri: string;
    gcs_blob_name: string;
    size_bytes: number;
    content_type: string;
    file_type: string;
    db_id: string;
  }>;
  vertex_ai_import: {
    triggered: boolean;
    operation_name: string | null;
    status_message: string;
  };
}

export interface DeleteResponse {
  status: string;
  message: string;
  deleted: {
    documents_deleted_from_db?: number;
    files_deleted_from_gcs?: number;
    vertex_ai_deletions_queued?: number;
    collection_id?: string;
    collection_name?: string;
    document_id?: string;
    original_filename?: string;
    gcs_blob_name?: string;
    vertex_ai_doc_id?: string;
  };
}

export interface ApiError {
  detail: string;
}

export interface HealthResponse {
  status: string;
  gcp_project: string;
  datastore_id: string;
  bucket: string;
}
