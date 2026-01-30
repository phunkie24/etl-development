"""
Logging configuration using structlog for structured logging.
Provides context-aware logging suitable for Azure Functions.
"""
import logging
import sys
from typing import Any, Dict
import structlog


def configure_logging(log_level: str = "INFO") -> structlog.BoundLogger:
    """
    Configure structured logging with appropriate processors.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger instance
    """
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper())
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    return structlog.get_logger()


def get_logger(name: str = __name__) -> structlog.BoundLogger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return structlog.get_logger(name)


class LogContext:
    """Context manager for adding structured context to logs."""
    
    def __init__(self, logger: structlog.BoundLogger, **context: Any):
        """
        Initialize log context.
        
        Args:
            logger: Logger instance
            **context: Key-value pairs to add to log context
        """
        self.logger = logger
        self.context = context
        self.bound_logger = None
    
    def __enter__(self) -> structlog.BoundLogger:
        """Enter context and return bound logger."""
        self.bound_logger = self.logger.bind(**self.context)
        return self.bound_logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context."""
        if exc_type is not None:
            self.bound_logger.error(
                "Exception in log context",
                exc_type=exc_type.__name__,
                exc_value=str(exc_val)
            )
        return False
