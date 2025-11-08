"""Controller for Gemini File API operations."""

import logging
import mimetypes
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

import httpx
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Gemini File API base URL
GEMINI_FILE_API_BASE = "https://generativelanguage.googleapis.com"

# Allowed file extensions
ALLOWED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


class GeminiFileController:
    """Controller for Gemini File operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize Gemini File controller.

        Args:
            db: MongoDB database instance
        """
        self.db = db

    async def upload_file(
        self, file_content: bytes, filename: str, username: str, user_email: str
    ) -> Dict:
        """
        Upload file to Gemini File API and save to database.

        Args:
            file_content: File content as bytes
            filename: Original filename
            username: Username who uploaded
            user_email: Email of user who uploaded

        Returns:
            Dictionary with file_id, gemini_file data, and metadata
        """
        # Validate file type
        if not any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
            )

        # Validate file size
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413, detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB"
            )

        # Determine MIME type
        mime_type = self._get_mime_type(filename)

        # Upload to Gemini File API
        gemini_response = await self._upload_to_gemini_api(file_content, filename, mime_type)
        file_data = gemini_response.get("file", {})

        # Generate unique ID for database
        file_id = str(uuid.uuid4())

        # Create database record
        file_record = {
            "_id": file_id,
            "gemini_file_name": file_data.get("name"),
            "gemini_uri": file_data.get("uri"),
            "original_filename": filename,
            "mime_type": file_data.get("mimeType", mime_type),
            "size_bytes": int(file_data.get("sizeBytes", len(file_content))),
            "sha256_hash": file_data.get("sha256Hash"),
            "state": file_data.get("state", "ACTIVE"),
            "source": file_data.get("source", "UPLOADED"),
            "create_time": file_data.get("createTime"),
            "update_time": file_data.get("updateTime"),
            "expiration_time": file_data.get("expirationTime"),
            "uploaded_by": username,
            "updatedby": user_email,
            "uploaded_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        # Save to database
        await self.db.gemini_files.insert_one(file_record)

        logger.info(f"File uploaded and saved: {file_id}")

        return {
            "file_id": file_id,
            "gemini_file": file_data,
            "uploaded_by": username,
            "updatedby": user_email,
            "message": "File uploaded successfully to Gemini File API",
        }

    async def list_files(self, page: int, page_size: int) -> Dict:
        """
        List all Gemini files with pagination.

        Args:
            page: Page number (starts from 1)
            page_size: Number of items per page

        Returns:
            Dictionary with data and pagination info
        """
        skip = (page - 1) * page_size

        # Get total count
        total_count = await self.db.gemini_files.count_documents({})

        # Get paginated results
        cursor = (
            self.db.gemini_files.find().sort("uploaded_at", -1).skip(skip).limit(page_size)
        )
        files = await cursor.to_list(length=page_size)

        # Calculate pagination info
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0

        return {
            "data": files,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1,
            },
        }

    async def get_file(self, file_id: str) -> Dict:
        """
        Get a specific Gemini file by ID.

        Args:
            file_id: The file ID

        Returns:
            File record dictionary

        Raises:
            HTTPException: If file not found
        """
        file_record = await self.db.gemini_files.find_one({"_id": file_id})

        if not file_record:
            raise HTTPException(status_code=404, detail="Gemini file not found")

        return file_record

    async def delete_file(self, file_id: str) -> Dict:
        """
        Delete a Gemini file record from database.

        Args:
            file_id: The file ID to delete

        Returns:
            Dictionary with deletion confirmation

        Raises:
            HTTPException: If file not found
        """
        logger.info(f"Deleting Gemini file: {file_id}")

        # Find the file record
        file_record = await self.db.gemini_files.find_one({"_id": file_id})

        if not file_record:
            raise HTTPException(status_code=404, detail="Gemini file not found")

        # Delete from database
        result = await self.db.gemini_files.delete_one({"_id": file_id})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Gemini file not found")

        logger.info(f"Gemini file deleted: {file_id}")

        return {
            "file_id": file_id,
            "message": "Gemini file record deleted successfully",
            "note": "File in Gemini File API will expire automatically based on expirationTime",
        }

    async def _upload_to_gemini_api(
        self, file_content: bytes, filename: str, mime_type: str
    ) -> Dict:
        """
        Upload file to Gemini File API.

        Args:
            file_content: File content as bytes
            filename: Original filename
            mime_type: MIME type of the file

        Returns:
            File metadata from Gemini API response

        Raises:
            HTTPException: If upload fails
        """
        if not settings.google_api_key:
            raise ValueError(
                "GOOGLE_API_KEY not configured. Please set it in environment variables."
            )

        try:
            # Upload to Gemini File API
            upload_url = f"{GEMINI_FILE_API_BASE}/upload/v1beta/files"
            params = {"key": settings.google_api_key}

            # Prepare multipart form data
            # Gemini API expects the field name to be the MIME type (e.g., "image/jpeg")
            files = {mime_type: (filename, file_content, mime_type)}

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(upload_url, params=params, files=files)

                response.raise_for_status()
                result = response.json()

                logger.info(f"Uploaded to Gemini File API: {result.get('file', {}).get('name')}")
                return result

        except httpx.HTTPStatusError as e:
            logger.error(f"Gemini File API upload failed: {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Failed to upload to Gemini File API: {e.response.text}",
            )
        except Exception as e:
            logger.error(f"Failed to upload to Gemini File API: {e}")
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    def _get_mime_type(self, filename: str) -> str:
        """
        Determine MIME type from filename.

        Args:
            filename: File filename

        Returns:
            MIME type string
        """
        mime_type, _ = mimetypes.guess_type(filename)
        if not mime_type:
            # Default based on extension
            if filename.lower().endswith((".jpg", ".jpeg")):
                mime_type = "image/jpeg"
            elif filename.lower().endswith(".png"):
                mime_type = "image/png"
            elif filename.lower().endswith(".gif"):
                mime_type = "image/gif"
            elif filename.lower().endswith(".bmp"):
                mime_type = "image/bmp"
            elif filename.lower().endswith(".webp"):
                mime_type = "image/webp"
            else:
                mime_type = "image/jpeg"  # Default

        return mime_type

