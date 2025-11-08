"""Q&A request and response models."""

from typing import Optional

from pydantic import BaseModel, Field


class TextQuestionRequest(BaseModel):
    """Request model for text Q&A."""

    question: str = Field(..., description="Your question text", min_length=1)


class TextQuestionResponse(BaseModel):
    """Response model for text Q&A."""

    question: str = Field(..., description="The question asked")
    answer: str = Field(..., description="AI-generated answer")
    model: str = Field(default="gemini-2.0-flash-exp", description="Model used")
    user_id: str = Field(..., description="User ID who asked the question")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "question": "What is artificial intelligence?",
                "answer": "Artificial intelligence (AI) is...",
                "model": "gemini-2.0-flash-exp",
                "user_id": "abc-123-def-456",
            }
        }


class ImageQuestionRequest(BaseModel):
    """Request model for image Q&A."""

    question: str = Field(..., description="Question about the image", min_length=1)


class ImageQuestionResponse(BaseModel):
    """Response model for image Q&A."""

    question: str = Field(..., description="The question asked")
    answer: str = Field(..., description="AI-generated answer based on image")
    model: str = Field(default="gemini-2.0-flash-exp", description="Model used")
    filename: str = Field(..., description="Uploaded image filename")
    user_id: str = Field(..., description="User ID who asked the question")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "question": "What is in this image?",
                "answer": "This image shows...",
                "model": "gemini-2.0-flash-exp",
                "filename": "image.jpg",
                "user_id": "abc-123-def-456",
            }
        }


class PDFQuestionRequest(BaseModel):
    """Request model for PDF Q&A."""

    question: str = Field(..., description="Question about the PDF", min_length=1)


class PDFQuestionResponse(BaseModel):
    """Response model for PDF Q&A."""

    question: str = Field(..., description="The question asked")
    answer: str = Field(..., description="AI-generated answer based on PDF")
    model: str = Field(default="gemini-2.0-flash-exp", description="Model used")
    filename: str = Field(..., description="Uploaded PDF filename")
    pages: int = Field(..., description="Number of pages in PDF")
    resolution: str = Field(default="8K Ultra HD (7680px width)", description="Image resolution")
    user_id: str = Field(..., description="User ID who asked the question")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "question": "What are the main points in this document?",
                "answer": "The document discusses...",
                "model": "gemini-2.0-flash-exp",
                "filename": "document.pdf",
                "pages": 5,
                "resolution": "8K Ultra HD (7680px width)",
                "user_id": "abc-123-def-456",
            }
        }

