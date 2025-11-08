"""Fine-tuning models and requests."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FineTuneDataSource(str, Enum):
    """Data source for fine-tuning."""

    AUDIT_LOGS = "audit_logs"
    UPLOADED_IMAGES = "uploaded_images"
    EXISTING_DOCUMENTS = "existing_documents"
    MIXED = "mixed"


class FineTuneStatus(str, Enum):
    """Fine-tuning job status."""

    PENDING = "pending"
    PREPARING_DATA = "preparing_data"
    UPLOADING_TO_GCS = "uploading_to_gcs"
    TRAINING = "training"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ImageTrainingData(BaseModel):
    """Image data for fine-tuning."""

    image_path: str = Field(..., description="Path to uploaded image")
    gcs_uri: Optional[str] = Field(None, description="GCS URI after upload")
    prompt: str = Field(..., description="Training prompt for this image")
    expected_output: str = Field(..., description="Expected model output")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class FineTuneRequest(BaseModel):
    """Request to start fine-tuning job."""

    job_name: str = Field(..., description="Name for the fine-tuning job")
    base_model: str = Field(
        default="gemini-1.5-pro", description="Base model to fine-tune"
    )
    data_source: FineTuneDataSource = Field(
        default=FineTuneDataSource.AUDIT_LOGS,
        description="Source of training data",
    )
    
    # Training parameters
    epochs: int = Field(default=3, ge=1, le=20, description="Number of training epochs")
    learning_rate: float = Field(
        default=0.0001, ge=0.00001, le=0.01, description="Learning rate"
    )
    batch_size: int = Field(default=8, ge=1, le=128, description="Batch size")
    
    # Data parameters
    min_samples: int = Field(
        default=100, ge=10, description="Minimum number of training samples"
    )
    include_images: bool = Field(
        default=False, description="Whether to include image training data"
    )
    
    # Image-specific parameters
    image_training_data: Optional[List[ImageTrainingData]] = Field(
        None, description="Image training examples (if include_images=True)"
    )
    
    # Filtering
    min_confidence: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum confidence for audit log samples",
    )
    
    # GCS configuration
    gcs_bucket: Optional[str] = Field(
        None, description="GCS bucket name (uses default if not provided)"
    )
    gcs_dataset_path: Optional[str] = Field(
        None, description="GCS path for dataset"
    )
    
    # Metadata
    description: Optional[str] = Field(None, description="Job description")
    tags: List[str] = Field(default_factory=list, description="Tags for organization")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "job_name": "compliance_qa_v2",
                "base_model": "gemini-1.5-pro",
                "data_source": "mixed",
                "epochs": 5,
                "learning_rate": 0.0001,
                "min_samples": 200,
                "include_images": True,
                "description": "Fine-tune for compliance Q&A with image support",
                "tags": ["compliance", "qa", "images"],
            }
        }


class FineTuneJob(BaseModel):
    """Fine-tuning job record."""

    id: str = Field(alias="_id")
    job_name: str
    status: FineTuneStatus
    base_model: str
    
    # Job details
    data_source: str
    num_training_samples: Optional[int] = None
    num_image_samples: Optional[int] = None
    
    # Training parameters
    epochs: int
    learning_rate: float
    batch_size: int
    
    # GCS paths
    gcs_dataset_uri: Optional[str] = None
    gcs_images_uploaded: List[str] = Field(default_factory=list)
    
    # Results
    tuned_model_id: Optional[str] = None
    tuned_model_endpoint: Optional[str] = None
    
    # Metrics
    training_metrics: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # User info
    created_by: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    class Config:
        """Pydantic config."""

        populate_by_name = True


class FineTuneResponse(BaseModel):
    """Response after starting fine-tuning job."""

    job_id: str = Field(..., description="Fine-tuning job ID")
    status: str = Field(..., description="Current job status")
    message: str = Field(..., description="Status message")
    estimated_completion_time: Optional[str] = Field(
        None, description="Estimated completion time"
    )
    monitor_url: Optional[str] = Field(None, description="URL to monitor job progress")


class FineTuneJobStatus(BaseModel):
    """Fine-tuning job status response."""

    job_id: str
    job_name: str
    status: str
    progress_percentage: Optional[float] = Field(
        None, ge=0, le=100, description="Progress percentage"
    )
    current_step: Optional[str] = None
    num_samples: Optional[int] = None
    epochs_completed: Optional[int] = None
    total_epochs: Optional[int] = None
    tuned_model_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    estimated_completion: Optional[datetime] = None


class ImageUploadResponse(BaseModel):
    """Response after uploading image for fine-tuning."""

    image_id: str = Field(..., description="Uploaded image ID")
    filename: str = Field(..., description="Original filename")
    local_path: str = Field(..., description="Local storage path")
    gcs_uri: Optional[str] = Field(None, description="GCS URI (if uploaded)")
    size_bytes: int = Field(..., description="File size in bytes")
    format: str = Field(..., description="Image format")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

