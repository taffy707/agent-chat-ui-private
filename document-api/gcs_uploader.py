"""
Google Cloud Storage uploader utility.

Handles uploading files to GCS bucket with unique filenames.
Based on patterns from vais-building-blocks/ingesting_unstructured_documents_with_metadata.ipynb
"""

import logging
import uuid
from pathlib import Path
from typing import Optional

from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError

logger = logging.getLogger(__name__)


class GCSUploader:
    """Handles file uploads to Google Cloud Storage."""

    def __init__(self, project_id: str, bucket_name: str):
        """
        Initialize GCS uploader.

        Args:
            project_id: Google Cloud project ID
            bucket_name: GCS bucket name for storing documents
        """
        self.project_id = project_id
        self.bucket_name = bucket_name
        self.client = storage.Client(project=project_id)
        self.bucket = self.client.bucket(bucket_name)

    def generate_unique_filename(self, original_filename: str) -> str:
        """
        Generate a unique filename to prevent collisions.

        Args:
            original_filename: Original file name uploaded by user

        Returns:
            Unique filename with UUID prefix and original extension
        """
        file_path = Path(original_filename)
        file_extension = file_path.suffix
        unique_id = uuid.uuid4().hex[:12]
        # Format: <uuid>_<original_name>.<ext>
        return f"{unique_id}_{file_path.stem}{file_extension}"

    def upload_file(
        self,
        file_content: bytes,
        original_filename: str,
        content_type: str,
        metadata: dict = None
    ) -> tuple[str, str]:
        """
        Upload file to GCS bucket with optional metadata.

        Args:
            file_content: File content as bytes
            original_filename: Original filename
            content_type: MIME type of the file
            metadata: Optional custom metadata (e.g., collection info, user_id)

        Returns:
            Tuple of (gcs_uri, blob_name)

        Raises:
            GoogleCloudError: If upload fails
        """
        try:
            # Generate unique filename
            blob_name = self.generate_unique_filename(original_filename)

            # Create blob and upload
            blob = self.bucket.blob(blob_name)

            # Set custom metadata if provided
            if metadata:
                blob.metadata = metadata
                logger.info(f"Setting GCS metadata: {metadata}")

            blob.upload_from_string(file_content, content_type=content_type)

            # Construct GCS URI
            gcs_uri = f"gs://{self.bucket_name}/{blob_name}"

            logger.info(f"Successfully uploaded file to {gcs_uri}")
            return gcs_uri, blob_name

        except GoogleCloudError as e:
            logger.error(f"Failed to upload file to GCS: {str(e)}")
            raise

    def delete_file(self, blob_name: str) -> bool:
        """
        Delete a file from GCS bucket.

        Args:
            blob_name: Name of the blob to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            blob = self.bucket.blob(blob_name)
            blob.delete()
            logger.info(f"Successfully deleted {blob_name} from GCS")
            return True
        except GoogleCloudError as e:
            logger.error(f"Failed to delete file from GCS: {str(e)}")
            return False

    def ensure_bucket_exists(self) -> bool:
        """
        Check if bucket exists, create if it doesn't.

        Returns:
            True if bucket exists or was created successfully
        """
        try:
            if not self.bucket.exists():
                logger.info(f"Creating bucket: {self.bucket_name}")
                self.bucket = self.client.create_bucket(self.bucket_name)
                logger.info(f"Bucket {self.bucket_name} created successfully")
            return True
        except GoogleCloudError as e:
            logger.error(f"Failed to ensure bucket exists: {str(e)}")
            return False
