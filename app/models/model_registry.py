"""Model registry data models."""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class ModelRegistryCreate(BaseModel):
    """Model for registering a new model."""

    model_id: str = Field(..., description="Unique model identifier")
    model_type: str = Field(
        ..., description="Model type: 'embedding', 'qa', 'fine_tuned', etc."
    )
    model_name: str = Field(..., description="Human-readable model name")
    model_provider: str = Field(..., description="Provider: 'vertex_ai', 'openai', 'local', etc.")
    configuration: Dict[str, Any] = Field(default_factory=dict, description="Model configuration")
    performance_metrics: Dict[str, float] = Field(
        default_factory=dict, description="Performance metrics"
    )
    description: Optional[str] = Field(default=None, description="Model description")


class ModelRegistry(BaseModel):
    """Model registry entry."""

    id: str = Field(alias="_id")
    model_id: str
    model_type: str
    model_name: str
    model_provider: str
    configuration: Dict[str, Any] = Field(default_factory=dict)
    performance_metrics: Dict[str, float] = Field(default_factory=dict)
    description: Optional[str] = None
    status: str = Field(
        default="active", description="Status: 'active', 'inactive', 'deprecated'"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = Field(default=None, description="User who registered the model")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "_id": "507f1f77bcf86cd799439011",
                "model_id": "gemini-1.5-pro-fine-tuned-001",
                "model_type": "qa",
                "model_name": "Gemini Pro Fine-Tuned v1",
                "model_provider": "vertex_ai",
                "configuration": {"temperature": 0.7, "max_tokens": 1024},
                "performance_metrics": {"accuracy": 0.92, "latency_ms": 250},
                "status": "active",
                "created_at": "2025-11-07T10:00:00Z",
            }
        }
    )

