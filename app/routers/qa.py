"""Q&A API endpoints (Router/View layer)."""

import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.controllers.qa import QAController
from app.middleware.auth import get_current_active_user
from app.models.qa import (
    ImageQuestionResponse,
    PDFQuestionResponse,
    TextQuestionResponse,
)
from app.models.user import UserResponse

logger = logging.getLogger(__name__)
router = APIRouter()


def get_controller() -> QAController:
    """Dependency to get QAController instance."""
    return QAController()


@router.post("/qa/text", response_model=TextQuestionResponse)
async def ask_text_question(
    question: str = Form(..., description="Your question"),
    controller: QAController = Depends(get_controller),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Ask a text question (no file upload).
    
    - **question**: Your question text
    
    Returns AI-generated answer using Gemini.
    """
    try:
        return await controller.ask_text_question(question, current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text Q&A failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/qa/image", response_model=ImageQuestionResponse)
async def ask_image_question(
    file: UploadFile = File(..., description="Image file"),
    question: str = Form(..., description="Question about the image"),
    controller: QAController = Depends(get_controller),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Upload an image and ask questions about it.
    
    - **file**: Image file (JPEG, PNG, etc.)
    - **question**: Your question about the image
    
    Returns AI-generated answer based on image analysis with Gemini.
    """
    try:
        # Read file content
        contents = await file.read()
        
        # Process via controller
        return await controller.ask_image_question(
            contents, file.filename, question, current_user.id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image Q&A failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/qa/pdf", response_model=PDFQuestionResponse)
async def ask_pdf_question(
    file: UploadFile = File(..., description="PDF file"),
    question: str = Form(..., description="Question about the PDF"),
    controller: QAController = Depends(get_controller),
    current_user: UserResponse = Depends(get_current_active_user),
):
    """
    Upload a PDF and ask questions about it.
    
    **Special Feature**: Converts PDF pages to ultra HD 8K resolution images
    before sending to Gemini for best quality analysis.
    
    - **file**: PDF file
    - **question**: Your question about the PDF content
    
    Returns AI-generated answer based on PDF analysis with Gemini.
    """
    try:
        # Read file content
        contents = await file.read()
        
        # Process via controller
        return await controller.ask_pdf_question(
            contents, file.filename, question, current_user.id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF Q&A failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
