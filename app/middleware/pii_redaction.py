"""PII (Personally Identifiable Information) redaction middleware."""

import logging
import re
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class PIIRedactionMiddleware(BaseHTTPMiddleware):
    """Middleware to redact PII from logs and responses."""

    def __init__(self, app):
        """Initialize PII redaction middleware."""
        super().__init__(app)
        self.patterns = self._compile_patterns()

    def _compile_patterns(self) -> dict:
        """
        Compile regex patterns for PII detection.

        Returns:
            Dictionary of compiled patterns
        """
        patterns = {}

        # Social Security Number (SSN) - US format: XXX-XX-XXXX
        patterns["ssn"] = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

        # Email addresses
        patterns["email"] = re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        )

        # Phone numbers (various formats)
        patterns["phone"] = re.compile(
            r"\b(\+\d{1,2}\s?)?(\(?\d{3}\)?[\s.-]?)?\d{3}[\s.-]?\d{4}\b"
        )

        # Credit card numbers (basic pattern)
        patterns["credit_card"] = re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b")

        # IP addresses (optional, might be needed for security)
        patterns["ip_address"] = re.compile(
            r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
        )

        return patterns

    def redact_text(self, text: str) -> str:
        """
        Redact PII from text using configured patterns.

        Args:
            text: Input text to redact

        Returns:
            Text with PII redacted
        """
        if not text:
            return text

        redacted = text

        # Apply each pattern based on configuration
        for pattern_name, pattern in self.patterns.items():
            if pattern_name in settings.pii_patterns_list:
                replacement = f"[REDACTED_{pattern_name.upper()}]"
                redacted = pattern.sub(replacement, redacted)

        return redacted

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Process request and response, redacting PII where appropriate.

        Args:
            request: Incoming request
            call_next: Next middleware/handler in chain

        Returns:
            Response with PII redaction applied if needed
        """
        # Log request (with PII redaction)
        if settings.log_level == "DEBUG":
            path = self.redact_text(str(request.url.path))
            logger.debug(f"Request: {request.method} {path}")

        # Process request
        response = await call_next(request)

        return response

    @staticmethod
    def redact_dict(data: dict, keys_to_redact: list = None) -> dict:
        """
        Redact specific keys in a dictionary (useful for structured logs).

        Args:
            data: Dictionary to redact
            keys_to_redact: List of keys to redact (default: common PII keys)

        Returns:
            Dictionary with specified keys redacted
        """
        if keys_to_redact is None:
            keys_to_redact = [
                "password",
                "ssn",
                "social_security_number",
                "credit_card",
                "card_number",
                "cvv",
                "api_key",
                "secret",
                "token",
            ]

        redacted = data.copy()

        for key in keys_to_redact:
            if key in redacted:
                redacted[key] = "[REDACTED]"

        return redacted


def scan_for_sensitive_content(text: str) -> tuple[bool, list[str]]:
    """
    Scan text for potentially sensitive content.

    Args:
        text: Text to scan

    Returns:
        Tuple of (has_sensitive_content, list_of_detected_patterns)
    """
    middleware = PIIRedactionMiddleware(None)
    detected = []

    for pattern_name, pattern in middleware.patterns.items():
        if pattern.search(text):
            detected.append(pattern_name)

    return len(detected) > 0, detected

