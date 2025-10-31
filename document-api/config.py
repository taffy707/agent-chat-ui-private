"""
Configuration module for FastAPI Document Upload Service.

Loads configuration from environment variables and validates settings.
"""

import os
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Google Cloud Project Settings
    GCP_PROJECT_ID: str
    VERTEX_AI_DATA_STORE_ID: str
    VERTEX_AI_LOCATION: str = "global"
    GCS_BUCKET_NAME: str

    # PostgreSQL Database Settings
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    # Supported file types
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt", ".html", ".htm"]
    ALLOWED_MIME_TYPES: List[str] = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "text/html",
    ]

    # File size limits (in bytes) - 32MB default
    MAX_FILE_SIZE: int = 32 * 1024 * 1024

    # API Settings
    API_TITLE: str = "Document Upload API for Vertex AI Search"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = (
        "FastAPI service for uploading documents to Google Cloud Storage "
        "and automatically indexing them in Vertex AI Search"
    )

    # Deletion Queue Settings (optimized for Vertex AI indexing time: 2-10 minutes)
    DELETION_QUEUE_WORKER_INTERVAL: int = 60  # Check queue every 60 seconds
    DELETION_QUEUE_MAX_ATTEMPTS: int = 10  # Maximum retry attempts
    DELETION_QUEUE_INITIAL_DELAY: int = 120  # First retry after 2 minutes

    class Config:
        env_file = ".env"
        case_sensitive = True


# Initialize settings
settings = Settings()
