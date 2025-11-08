"""Controller for Q&A operations."""

import io
import logging
import os
import tempfile
from typing import Dict, List

import fitz  # PyMuPDF
from fastapi import HTTPException
from PIL import Image

from app.services.gemini_service import GeminiService

logger = logging.getLogger(__name__)

# Allowed file extensions
ALLOWED_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]
TARGET_WIDTH_8K = 7680  # 8K resolution width


class QAController:
    """Controller for Q&A operations."""

    def __init__(self):
        """Initialize QA controller."""
        self.gemini_service = GeminiService()

    async def ask_text_question(self, question: str, user_id: str) -> Dict:
        """
        Ask a text-only question.

        Args:
            question: The question text
            user_id: User ID who asked the question

        Returns:
            Dictionary with question, answer, model, and user_id
        """
        try:
            answer = await self.gemini_service.ask_question(question)

            return {
                "question": question,
                "answer": answer,
                "model": "gemini-2.0-flash-exp",
                "user_id": user_id,
            }
        except Exception as e:
            logger.error(f"Text Q&A failed: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to process question: {str(e)}")

    async def ask_image_question(
        self, file_content: bytes, filename: str, question: str, user_id: str
    ) -> Dict:
        """
        Ask a question about an image.

        Args:
            file_content: Image file content as bytes
            filename: Original filename
            question: Question about the image
            user_id: User ID who asked the question

        Returns:
            Dictionary with question, answer, model, filename, and user_id

        Raises:
            HTTPException: If file type is invalid or processing fails
        """
        try:
            # Validate file type
            if not any(filename.lower().endswith(ext) for ext in ALLOWED_IMAGE_EXTENSIONS):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}",
                )

            # Read and process image
            image = Image.open(io.BytesIO(file_content))

            # Convert to RGB if needed
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Use Gemini for image + question
            answer = await self.gemini_service.ask_with_image(question, image)

            return {
                "question": question,
                "answer": answer,
                "model": "gemini-2.0-flash-exp",
                "filename": filename,
                "user_id": user_id,
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Image Q&A failed: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to process image question: {str(e)}")

    async def ask_pdf_question(
        self, file_content: bytes, filename: str, question: str, user_id: str
    ) -> Dict:
        """
        Ask a question about a PDF (converted to 8K images).

        Args:
            file_content: PDF file content as bytes
            filename: Original filename
            question: Question about the PDF
            user_id: User ID who asked the question

        Returns:
            Dictionary with question, answer, model, filename, pages, resolution, and user_id

        Raises:
            HTTPException: If file type is invalid or processing fails
        """
        try:
            # Validate file type
            if not filename.lower().endswith(".pdf"):
                raise HTTPException(status_code=400, detail="File must be a PDF")

            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(file_content)
                tmp_path = tmp_file.name

            try:
                # Convert PDF to 8K images
                images = self._convert_pdf_to_8k_images(tmp_path)
                page_count = len(images)

                logger.info(f"Converted PDF with {page_count} pages to 8K images")

                # Use Gemini for PDF analysis with 8K images
                answer = await self.gemini_service.ask_with_pdf_images(question, images)

                return {
                    "question": question,
                    "answer": answer,
                    "model": "gemini-2.0-flash-exp",
                    "filename": filename,
                    "pages": page_count,
                    "resolution": "8K Ultra HD (7680px width)",
                    "user_id": user_id,
                }

            finally:
                # Clean up temp file
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"PDF Q&A failed: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to process PDF question: {str(e)}")

    def _convert_pdf_to_8k_images(self, pdf_path: str) -> List[Image.Image]:
        """
        Convert PDF pages to ultra HD 8K resolution images.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of PIL Image objects (one per page)
        """
        pdf_document = fitz.open(pdf_path)
        page_count = len(pdf_document)

        logger.info(f"Converting PDF with {page_count} pages to 8K images")

        images = []

        for page_num in range(page_count):
            page = pdf_document[page_num]

            # Calculate zoom to achieve 8K resolution
            # Standard PDF page is ~595x842 points (A4)
            zoom_x = TARGET_WIDTH_8K / page.rect.width
            zoom_y = zoom_x  # Maintain aspect ratio

            mat = fitz.Matrix(zoom_x, zoom_y)

            # Render page to pixmap (image) at high resolution
            pix = page.get_pixmap(matrix=mat, alpha=False)

            # Convert to PIL Image
            img_data = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_data))

            logger.info(
                f"Page {page_num + 1} converted to {image.size[0]}x{image.size[1]} (8K)"
            )
            images.append(image)

        pdf_document.close()

        return images

