"""Gemini File models for request/response validation."""

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field


class GeminiFileResponse(BaseModel):
    """Response model for Gemini file upload."""

    file_id: str = Field(..., description="Unique file ID in our database")
    gemini_file: Dict = Field(..., description="Gemini File API response")
    uploaded_by: str = Field(..., description="Username who uploaded the file")
    updatedby: str = Field(..., description="Email of user who uploaded")
    message: str = Field(..., description="Success message")


class GeminiFileRecord(BaseModel):
    """Database record model for Gemini files."""

    _id: str = Field(..., alias="id", description="Unique file ID")
    gemini_file_name: str = Field(..., description="Gemini file name (e.g., 'files/8ekbyqh6fmod')")
    gemini_uri: str = Field(..., description="Full URI to access the file")
    original_filename: str = Field(..., description="Original uploaded filename")
    mime_type: str = Field(..., description="File MIME type")
    size_bytes: int = Field(..., description="File size in bytes")
    sha256_hash: Optional[str] = Field(None, description="File SHA256 hash")
    state: str = Field(default="ACTIVE", description="File state")
    source: str = Field(default="UPLOADED", description="File source")
    create_time: Optional[str] = Field(None, description="Gemini creation time")
    update_time: Optional[str] = Field(None, description="Gemini update time")
    expiration_time: Optional[str] = Field(None, description="File expiration time")
    uploaded_by: str = Field(..., description="Username who uploaded")
    updatedby: str = Field(..., description="Email of user who uploaded")
    uploaded_at: datetime = Field(..., description="Upload timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        """Pydantic config."""

        populate_by_name = True
        json_schema_extra = {
            "example": {
                "_id": "abc-123-def-456",
                "gemini_file_name": "files/8ekbyqh6fmod",
                "gemini_uri": "https://generativelanguage.googleapis.com/v1beta/files/8ekbyqh6fmod",
                "original_filename": "image.jpg",
                "mime_type": "image/jpeg",
                "size_bytes": 898013,
                "sha256_hash": "ODE3NjU4YzE3ZjQyMTc1MmQyNDYxYjg1OGM3MTM4NDk0NDYyYjgxOTk0ZGZkNDllNjMwMTkwYzAyODI4OGU3ZQ==",
                "state": "ACTIVE",
                "source": "UPLOADED",
                "uploaded_by": "johndoe",
                "updatedby": "john@example.com",
                "uploaded_at": "2025-11-07T18:11:52Z",
                "updated_at": "2025-11-07T18:11:52Z",
            }
        }


class PaginatedResponse(BaseModel):
    """Paginated response model."""

    data: list = Field(..., description="List of items")
    pagination: Dict = Field(..., description="Pagination metadata")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "data": [],
                "pagination": {
                    "page": 1,
                    "page_size": 10,
                    "total_count": 0,
                    "total_pages": 0,
                    "has_next": False,
                    "has_previous": False,
                },
            }
        }


class DeleteResponse(BaseModel):
    """Response model for delete operations."""

    file_id: str = Field(..., description="Deleted file ID")
    message: str = Field(..., description="Success message")
    note: Optional[str] = Field(None, description="Additional note")

