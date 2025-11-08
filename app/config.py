"""Application configuration management."""

import os
from typing import List, Optional

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        protected_namespaces=('settings_',)  # Fix Pydantic warning for model_adapter
    )

    # Environment
    environment: str = "development"

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_title: str = "Accord AI Compliance API"
    api_version: str = "1.0.0"
    log_level: str = "INFO"

    # MongoDB Configuration
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "accord_compliance"
    mongo_user: Optional[str] = None
    mongo_password: Optional[str] = None

    # Storage Configuration
    storage_path: str = "./storage"
    max_file_size_mb: int = 50

    # Model Configuration
    model_adapter: str = "local_stub"  # Options: local_stub, gemini_vertex
    embedding_adapter: str = "local_stub"  # Options: local_stub, gemini

    # Google Gemini API Configuration
    google_api_key: Optional[str] = None
    gemini_model_name: str = "gemini-2.0-flash-exp"
    gemini_embedding_model: str = "text-embedding-004"
    
    # Google Cloud / Vertex AI Configuration (Alternative)
    gemini_project: Optional[str] = None
    gemini_location: str = "us-central1"
    gemini_credentials_path: Optional[str] = None

    # Vector Search Configuration
    vector_dimension: int = 768
    top_k_results: int = 5
    similarity_threshold: float = 0.7

    # Security
    api_key: Optional[str] = None
    pii_redaction_enabled: bool = True
    pii_patterns: str = "ssn,email,phone,credit_card"

    # OCR Configuration
    tesseract_cmd: str = "tesseract"
    tesseract_lang: str = "eng"

    # Image Captioning
    image_caption_adapter: str = "local_stub"

    # Fine-Tuning
    gcs_bucket_name: Optional[str] = None
    fine_tune_dataset_path: str = "/tmp/finetune"

    # Audit Logging
    audit_enabled: bool = True
    audit_collection: str = "audit_logs"

    # CORS Configuration
    cors_origins: str = "http://localhost:3000,http://localhost:8000"
    
    # JWT Authentication
    jwt_secret_key: str = "your-secret-key-change-in-production-min-32-chars-long"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 1440  # 24 hours

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def pii_patterns_list(self) -> List[str]:
        """Parse PII patterns from comma-separated string."""
        return [pattern.strip() for pattern in self.pii_patterns.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        """Convert max file size from MB to bytes."""
        return self.max_file_size_mb * 1024 * 1024


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings instance."""
    return settings

