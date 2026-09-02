"""Logging configuration."""

import json
import logging
from datetime import UTC, datetime
from typing import Any

from core.config import get_settings


class JSONFormatter(logging.Formatter):
    """Format log records as JSON."""

    def format(self, record: logging.LogRecord) -> str:
        """Return a JSON log line."""
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def setup_logging() -> None:
    """Configure root logging once."""
    settings = get_settings()
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    root_logger.setLevel(level)

    handler = logging.StreamHandler()
    formatter: logging.Formatter
    if settings.debug:
        formatter = logging.Formatter("[%(levelname)s] %(message)s")
    else:
        formatter = JSONFormatter()

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger."""
    return logging.getLogger(name)
