"""Gemini File API endpoints (Router/View layer)."""

import logging

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from app.controllers.gemini_file import GeminiFileController
from app.database import get_database
from app.middleware.auth import get_current_active_user
from app.models.gemini_file import (
    DeleteResponse,
    GeminiFileResponse,
    PaginatedResponse,
)
from app.models.user import UserResponse

logger = logging.getLogger(__name__)
router = APIRouter()


def get_controller(db=Depends(get_database)) -> GeminiFileController:
    """Dependency to get GeminiFileController instance."""
    return GeminiFileController(db)


@router.post("/gemini-files/upload", response_model=GeminiFileResponse)
async def upload_image_to_gemini(
    file: UploadFile = File(..., description="Image file to upload"),
    controller: GeminiFileController = Depends(get_controller),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Upload an image to Gemini File API.
    
    **Parameters:**
    - **file**: Image file (JPEG, PNG, GIF, BMP, WEBP)
    
    **Returns:**
    - File metadata including URI, name, size, etc.
    
    **Example:**
    ```bash
    curl -X POST "http://localhost:8000/api/v1/gemini-files/upload" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -F "file=@image.jpg"
    ```
    """
    try:
        logger.info(f"Uploading image to Gemini File API: {file.filename}")
        
        # Read file content
        contents = await file.read()
        
        # Upload via controller
        result = await controller.upload_file(
            contents, file.filename, current_user.username, current_user.email
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload image to Gemini: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gemini-files", response_model=PaginatedResponse)
async def list_gemini_files(
    page: int = Query(default=1, ge=1, description="Page number (starts from 1)"),
    page_size: int = Query(default=10, ge=1, le=100, description="Number of items per page"),
    controller: GeminiFileController = Depends(get_controller),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Get all uploaded Gemini files with pagination.
    
    **Parameters:**
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 10, max: 100)
    
    **Example:**
    ```bash
    curl -X GET "http://localhost:8000/api/v1/gemini-files?page=1&page_size=10" \\
      -H "Authorization: Bearer YOUR_TOKEN"
    ```
    """
    try:
        return await controller.list_files(page, page_size)
        
    except Exception as e:
        logger.error(f"Failed to list Gemini files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gemini-files/{file_id}")
async def get_gemini_file(
    file_id: str,
    controller: GeminiFileController = Depends(get_controller),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Get a specific Gemini file by ID.
    
    **Parameters:**
    - **file_id**: The file ID
    
    **Example:**
    ```bash
    curl -X GET "http://localhost:8000/api/v1/gemini-files/abc-123" \\
      -H "Authorization: Bearer YOUR_TOKEN"
    ```
    """
    try:
        return await controller.get_file(file_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get Gemini file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/gemini-files/{file_id}", response_model=DeleteResponse)
async def delete_gemini_file(
    file_id: str,
    controller: GeminiFileController = Depends(get_controller),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Delete a Gemini file (removes from database only).
    
    **Note:** This only removes the record from our database. 
    The file in Gemini File API will expire automatically based on expirationTime.
    
    **Parameters:**
    - **file_id**: The file ID to delete
    
    **Example:**
    ```bash
    curl -X DELETE "http://localhost:8000/api/v1/gemini-files/abc-123" \\
      -H "Authorization: Bearer YOUR_TOKEN"
    ```
    """
    try:
        return await controller.delete_file(file_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete Gemini file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

