"""Structured logging utilities."""

import json
import logging
import sys
from datetime import datetime


class StructuredLogger:
    """JSON structured logger for agent operations."""

    def __init__(self, name: str = "knowledge-base-agent", level: str = "INFO"):
        """Initialize structured logger.

        Args:
            name: Logger name
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))

        # Remove existing handlers
        self.logger.handlers = []

        # Add JSON formatter
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        self.logger.addHandler(handler)

    def setLevel(self, level: str):
        """Set log level.

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.logger.setLevel(getattr(logging, level.upper()))
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        self.logger.addHandler(handler)

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log("DEBUG", message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log("ERROR", message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self._log("CRITICAL", message, **kwargs)

    def _log(self, level: str, message: str, **kwargs):
        """Internal log method."""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            **kwargs,
        }

        log_method = getattr(self.logger, level.lower())
        log_method(json.dumps(log_data))


class JSONFormatter(logging.Formatter):
    """JSON formatter for log records."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: Log record

        Returns:
            JSON formatted string
        """
        try:
            # Try to parse message as JSON
            log_data = json.loads(record.getMessage())
        except json.JSONDecodeError:
            # Fall back to simple format
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "level": record.levelname,
                "message": record.getMessage(),
            }

        return json.dumps(log_data)
