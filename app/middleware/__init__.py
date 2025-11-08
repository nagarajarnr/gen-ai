"""Middleware package."""

from app.middleware.pii_redaction import PIIRedactionMiddleware

__all__ = ["PIIRedactionMiddleware"]

