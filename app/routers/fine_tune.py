"""Simplified Fine-tuning API endpoints."""

import logging
import os
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, ConfigDict, Field

from app.config import get_settings
from app.database import get_database
from app.middleware.auth import get_current_active_user
from app.models.user import UserResponse

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()


class FineTuneStartRequest(BaseModel):
    """Request model for fine-tuning start endpoint."""
    
    model_config = ConfigDict(
        protected_namespaces=()  # Fix Pydantic warning for model_name
    )
    
    model_name: str = Field(..., description="Name for your fine-tuned model")
    base_model: str = Field(default="gemini-1.5-pro", description="Base model to fine-tune")
    epochs: int = Field(default=10, description="Number of training epochs")
    learning_rate: float = Field(default=0.001, description="Learning rate")
    
    @classmethod
    def as_form(
        cls,
        model_name: str = Form(..., description="Name for your fine-tuned model"),
        base_model: str = Form(default="gemini-1.5-pro", description="Base model to fine-tune"),
        epochs: int = Form(default=10, description="Number of training epochs"),
        learning_rate: float = Form(default=0.001, description="Learning rate"),
    ):
        """Create instance from form data."""
        return cls(
            model_name=model_name,
            base_model=base_model,
            epochs=epochs,
            learning_rate=learning_rate
        )


async def delete_from_gcs(gs_url: Optional[str], bucket_name: Optional[str] = None) -> bool:
    """
    Delete file from Google Cloud Storage.
    
    Args:
        gs_url: GS URL (gs://bucket/path) or None
        bucket_name: GCS bucket name (defaults to settings.gcs_bucket_name)
    
    Returns:
        True if deleted successfully, False otherwise
    """
    if not gs_url or not gs_url.startswith("gs://"):
        logger.warning(f"Invalid GS URL for deletion: {gs_url}")
        return False
    
    bucket_name = bucket_name or settings.gcs_bucket_name
    
    if not bucket_name:
        logger.warning("GCS bucket not configured, skipping deletion")
        return False
    
    try:
        from google.cloud import storage
        
        # Parse GS URL: gs://bucket/path
        parts = gs_url.replace("gs://", "").split("/", 1)
        if len(parts) != 2:
            logger.error(f"Invalid GS URL format: {gs_url}")
            return False
        
        gcs_bucket_name, gcs_path = parts
        
        # Initialize GCS client
        if settings.gemini_credentials_path and os.path.exists(settings.gemini_credentials_path):
            client = storage.Client.from_service_account_json(
                settings.gemini_credentials_path
            )
        else:
            client = storage.Client()
        
        # Delete file
        bucket = client.bucket(gcs_bucket_name)
        blob = bucket.blob(gcs_path)
        
        if blob.exists():
            blob.delete()
            logger.info(f"Deleted from GCS: {gs_url}")
            return True
        else:
            logger.warning(f"File not found in GCS: {gs_url}")
            return False
        
    except ImportError:
        logger.error("google-cloud-storage not installed. Install with: pip install google-cloud-storage")
        return False
    except Exception as e:
        logger.error(f"Failed to delete from GCS: {e}")
        return False


async def upload_to_gcs(
    local_path: str, gcs_path: str, bucket_name: Optional[str] = None
) -> Tuple[Optional[str], Optional[str]]:
    """
    Upload file to Google Cloud Storage and return both GS URL and HTTP URL.
    
    Args:
        local_path: Local file path to upload
        gcs_path: GCS destination path (without gs:// prefix)
        bucket_name: GCS bucket name (defaults to settings.gcs_bucket_name)
    
    Returns:
        Tuple of (gs_url, http_url) or (None, None) if GCS not configured
    """
    bucket_name = bucket_name or settings.gcs_bucket_name
    
    if not bucket_name:
        logger.warning("GCS bucket not configured, skipping upload")
        return None, None
    
    try:
        from google.cloud import storage
        
        # Initialize GCS client
        if settings.gemini_credentials_path and os.path.exists(settings.gemini_credentials_path):
            client = storage.Client.from_service_account_json(
                settings.gemini_credentials_path
            )
        else:
            # Use default credentials (e.g., from environment or metadata server)
            client = storage.Client()
        
        # Upload file
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(gcs_path)
        
        blob.upload_from_filename(local_path)
        
        # Make blob publicly readable (optional, adjust based on your needs)
        # blob.make_public()
        
        # Generate URLs
        gs_url = f"gs://{bucket_name}/{gcs_path}"
        http_url = f"https://storage.googleapis.com/{bucket_name}/{gcs_path}"
        
        logger.info(f"Uploaded to GCS: {gs_url}")
        logger.info(f"HTTP URL: {http_url}")
        
        return gs_url, http_url
        
    except ImportError:
        logger.error("google-cloud-storage not installed. Install with: pip install google-cloud-storage")
        return None, None
    except Exception as e:
        logger.error(f"Failed to upload to GCS: {e}")
        raise


@router.post("/finetune/upload-image")
async def upload_training_image(
    file: UploadFile = File(..., description="Image file for training"),
    prompt: str = Form(..., description="Training prompt for this image"),
    expected_output: str = Form(..., description="Expected model output"),
    db=Depends(get_database),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Upload an image to use in fine-tuning training data.
    
    **Parameters:**
    - **file**: Image file (JPEG, PNG, GIF, BMP)
    - **prompt**: What question/prompt to use with this image
    - **expected_output**: What the model should respond
    
    **Example:**
    ```bash
    curl -X POST "http://localhost:8000/api/v1/finetune/upload-image" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -F "file=@screenshot.png" \\
      -F "prompt=What issues are visible?" \\
      -F "expected_output=Missing logo and incorrect colors"
    ```
    """
    try:
        logger.info(f"Uploading training image: {file.filename}")
        
        # Validate file type
        allowed_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp"]
        if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Read file
        contents = await file.read()
        if len(contents) > 50 * 1024 * 1024:  # 50MB limit
            raise HTTPException(
                status_code=413,
                detail="File too large. Maximum size: 50MB"
            )
        
        # Generate unique ID
        image_id = str(uuid.uuid4())
        file_ext = file.filename.split(".")[-1]
        storage_filename = f"{image_id}.{file_ext}"
        
        # Create temporary file for upload
        os.makedirs("/app/storage/finetune", exist_ok=True)
        storage_path = f"/app/storage/finetune/{storage_filename}"
        
        # Save file locally first
        with open(storage_path, "wb") as f:
            f.write(contents)
        
        # Upload to GCS
        gcs_path = f"finetune/images/{storage_filename}"
        gs_url, http_url = await upload_to_gcs(storage_path, gcs_path)
        
        # Save to database with both URLs and updatedby email
        training_data = {
            "_id": image_id,
            "filename": file.filename,
            "storage_path": storage_path,
            "gs_url": gs_url,  # GS URL (gs://bucket/path)
            "http_url": http_url,  # HTTP URL (https://storage.googleapis.com/...)
            "prompt": prompt,
            "expected_output": expected_output,
            "size_bytes": len(contents),
            "format": file_ext.upper(),
            "uploaded_by": current_user.username,
            "updatedby": current_user.email,  # Store user email in updatedby field
            "uploaded_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        
        await db.training_images.insert_one(training_data)
        
        logger.info(f"Training image saved: {image_id}")
        if gs_url:
            logger.info(f"GCS URLs - GS: {gs_url}, HTTP: {http_url}")
        
        return {
            "image_id": image_id,
            "filename": file.filename,
            "storage_path": storage_path,
            "gs_url": gs_url,
            "http_url": http_url,
            "size_bytes": len(contents),
            "format": file_ext.upper(),
            "prompt": prompt,
            "expected_output": expected_output,
            "updatedby": current_user.email,
            "message": "Image uploaded successfully for fine-tuning"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload training image: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/finetune/start")
async def start_fine_tune(
    request: FineTuneStartRequest = Depends(FineTuneStartRequest.as_form),
    db=Depends(get_database),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Start a fine-tuning job with uploaded training images.
    
    **Parameters:**
    - **model_name**: Name for your custom model (e.g., "my-compliance-model-v1")
    - **base_model**: Base Gemini model (default: gemini-1.5-pro)
    - **epochs**: Training epochs (default: 10)
    - **learning_rate**: Learning rate (default: 0.001)
    
    **Example:**
    ```bash
    curl -X POST "http://localhost:8000/api/v1/finetune/start" \\
      -H "Authorization: Bearer YOUR_TOKEN" \\
      -F "model_name=my-custom-model" \\
      -F "epochs=10"
    ```
    """
    try:
        logger.info(f"Starting fine-tune job: {request.model_name}")
        
        # Count available training images
        image_count = await db.training_images.count_documents({})
        
        if image_count == 0:
            raise HTTPException(
                status_code=400,
                detail="No training images found. Please upload training data first."
            )
        
        logger.info(f"Found {image_count} training images")
        
        # Create job
        job_id = str(uuid.uuid4())
        
        job_data = {
            "_id": job_id,
            "model_name": request.model_name,
            "base_model": request.base_model,
            "status": "pending",
            "progress": 0,
            "epochs": request.epochs,
            "learning_rate": request.learning_rate,
            "training_images_count": image_count,
            "created_by": current_user.username,
            "created_at": datetime.now(timezone.utc),
            "started_at": None,
            "completed_at": None,
            "error": None,
        }
        
        await db.finetune_jobs.insert_one(job_data)
        
        # Note: Actual fine-tuning would happen here with Vertex AI
        # For now, we'll just create the job record
        logger.info(f"Fine-tune job created: {job_id}")
        
        return {
            "job_id": job_id,
            "model_name": request.model_name,
            "base_model": request.base_model,
            "status": "pending",
            "training_images_count": image_count,
            "epochs": request.epochs,
            "learning_rate": request.learning_rate,
            "created_at": job_data["created_at"],
            "message": "Fine-tuning job created successfully. Job will start processing shortly."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start fine-tune job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/finetune/status/{job_id}")
async def get_job_status(
    job_id: str,
    db=Depends(get_database),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Check the status of a fine-tuning job.
    
    **Parameters:**
    - **job_id**: The fine-tuning job ID
    
    **Returns:**
    - Job status, progress, metrics, etc.
    
    **Example:**
    ```bash
    curl -X GET "http://localhost:8000/api/v1/finetune/status/abc-123" \\
      -H "Authorization: Bearer YOUR_TOKEN"
    ```
    """
    try:
        logger.info(f"Checking status for job: {job_id}")
        
        job = await db.finetune_jobs.find_one({"_id": job_id})
        
        if not job:
            raise HTTPException(
                status_code=404,
                detail="Fine-tuning job not found"
            )
        
        return {
            "job_id": job["_id"],
            "model_name": job["model_name"],
            "base_model": job["base_model"],
            "status": job["status"],
            "progress": job["progress"],
            "epochs": job["epochs"],
            "training_images_count": job["training_images_count"],
            "created_at": job["created_at"],
            "started_at": job.get("started_at"),
            "completed_at": job.get("completed_at"),
            "error": job.get("error"),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
