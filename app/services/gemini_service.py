"""Gemini API service for Q&A and image analysis."""

import logging
from typing import List

import google.generativeai as genai
from PIL import Image

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class GeminiService:
    """Service for interacting with Google Gemini API."""
    
    def __init__(self):
        """Initialize Gemini service with API key."""
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY not configured. Please set it in environment variables.")
        
        genai.configure(api_key=settings.google_api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        logger.info("Gemini service initialized with model: gemini-2.0-flash-exp")
    
    async def ask_question(self, question: str) -> str:
        """
        Ask a text-only question to Gemini.
        
        Args:
            question: The question text
            
        Returns:
            Generated answer from Gemini
        """
        try:
            logger.info(f"Asking text question: {question[:100]}...")
            
            response = self.model.generate_content(question)
            answer = response.text
            
            logger.info(f"Received answer ({len(answer)} chars)")
            return answer
            
        except Exception as e:
            logger.error(f"Gemini text Q&A error: {e}")
            raise
    
    async def ask_with_image(self, question: str, image: Image.Image) -> str:
        """
        Ask a question about an image using Gemini's vision capabilities.
        
        Args:
            question: The question about the image
            image: PIL Image object
            
        Returns:
            Generated answer from Gemini based on image analysis
        """
        try:
            logger.info(f"Asking image question: {question[:100]}...")
            logger.info(f"Image size: {image.size[0]}x{image.size[1]}")
            
            # Gemini can handle images directly
            response = self.model.generate_content([question, image])
            answer = response.text
            
            logger.info(f"Received answer ({len(answer)} chars)")
            return answer
            
        except Exception as e:
            logger.error(f"Gemini image Q&A error: {e}")
            raise
    
    async def ask_with_pdf_images(self, question: str, images: List[Image.Image]) -> str:
        """
        Ask a question about a PDF (converted to 8K images).
        
        Args:
            question: The question about the PDF
            images: List of PIL Image objects (PDF pages as 8K images)
            
        Returns:
            Generated answer from Gemini based on multi-page PDF analysis
        """
        try:
            logger.info(f"Asking PDF question with {len(images)} pages (8K resolution)")
            logger.info(f"Question: {question[:100]}...")
            
            # For multi-page PDFs, we'll analyze all pages together
            # Gemini can handle multiple images in one request
            content = [f"Analyze this {len(images)}-page PDF document and answer: {question}"]
            
            # Add all page images
            for idx, image in enumerate(images):
                logger.info(f"Adding page {idx + 1} - Size: {image.size[0]}x{image.size[1]}")
                content.append(image)
            
            # Generate response with all pages
            response = self.model.generate_content(content)
            answer = response.text
            
            logger.info(f"Received answer from {len(images)} pages ({len(answer)} chars)")
            return answer
            
        except Exception as e:
            logger.error(f"Gemini PDF Q&A error: {e}")
            raise

