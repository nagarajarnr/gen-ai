"""FastAPI application entry point."""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import db_manager
from app.middleware.pii_redaction import PIIRedactionMiddleware
from app.routers import auth, fine_tune, gemini_files, qa
from app.utils.logger import setup_logging

settings = get_settings()
setup_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    logger.info("Starting Accord AI Compliance API")

    # Create storage directory
    os.makedirs(settings.storage_path, exist_ok=True)
    logger.info(f"Storage path: {settings.storage_path}")

    # Connect to MongoDB
    await db_manager.connect()

    yield

    # Shutdown
    logger.info("Shutting down Accord AI Compliance API")
    await db_manager.disconnect()


# Create FastAPI application
app = FastAPI(
    title="Accord AI Q&A & Fine-Tuning API",
    version=settings.api_version,
    description="AI-powered Q&A with Gemini 2.0 Flash (text, images, PDFs in 8K) and model fine-tuning",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add PII redaction middleware
if settings.pii_redaction_enabled:
    app.add_middleware(PIIRedactionMiddleware)

# Include routers
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(qa.router, prefix="/api/v1", tags=["Q&A"])
app.include_router(fine_tune.router, prefix="/api/v1", tags=["Fine-Tuning"])
app.include_router(gemini_files.router, prefix="/api/v1", tags=["Gemini Files"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Accord AI Compliance API",
        "version": settings.api_version,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check database connection
        db = db_manager.get_database()
        await db.command("ping")

        return {
            "status": "healthy",
            "environment": settings.environment,
            "database": "connected",
            "model_adapter": settings.model_adapter,
            "embedding_adapter": settings.embedding_adapter,
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
            },
        )


@app.get("/api/v1/config")
async def get_config():
    """Get current configuration (non-sensitive values only)."""
    return {
        "environment": settings.environment,
        "model_adapter": settings.model_adapter,
        "embedding_adapter": settings.embedding_adapter,
        "vector_dimension": settings.vector_dimension,
        "top_k_results": settings.top_k_results,
        "similarity_threshold": settings.similarity_threshold,
        "max_file_size_mb": settings.max_file_size_mb,
        "pii_redaction_enabled": settings.pii_redaction_enabled,
        "audit_enabled": settings.audit_enabled,
    }

