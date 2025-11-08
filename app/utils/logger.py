"""Structured logging configuration."""

import logging
import sys
from typing import Any, Dict

import structlog


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure structured logging with structlog.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer() if sys.stderr.isatty() else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> Any:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


def log_audit_event(
    event_type: str,
    user_id: str,
    details: Dict[str, Any],
    logger: Any = None,
) -> None:
    """
    Log an audit event with structured data.

    Args:
        event_type: Type of event (e.g., 'qa_query', 'document_ingest')
        user_id: User identifier
        details: Additional event details
        logger: Logger instance (will create one if not provided)
    """
    if logger is None:
        logger = get_logger("audit")

    logger.info(
        "audit_event",
        event_type=event_type,
        user_id=user_id,
        **details,
    )

