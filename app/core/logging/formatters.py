"""Log formatters for text and structured JSON output."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from app.core.logging.constants import (
    CORRELATION_ID_FIELD,
    DATE_FORMAT,
    TEXT_LOG_FORMAT,
)
from app.core.logging.correlation import resolve_correlation_id
from app.core.logging.masker import SensitiveDataMasker

_STANDARD_RECORD_FIELDS = frozenset(
    {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "message",
        CORRELATION_ID_FIELD,
    }
)


class TextLogFormatter(logging.Formatter):
    """Human-readable log formatter for console output."""

    def __init__(self) -> None:
        """Initialize the text formatter."""
        super().__init__(fmt=TEXT_LOG_FORMAT, datefmt=DATE_FORMAT)

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as human-readable text.

        Args:
            record: Log record to format.

        Returns:
            Formatted log line.
        """
        if not hasattr(record, CORRELATION_ID_FIELD):
            setattr(record, CORRELATION_ID_FIELD, resolve_correlation_id())
        return super().format(record)


class JsonLogFormatter(logging.Formatter):
    """Structured JSON log formatter for file output and log aggregation."""

    def __init__(self, masker: SensitiveDataMasker | None = None) -> None:
        """Initialize the JSON formatter.

        Args:
            masker: Optional masker applied to the final message field.
        """
        super().__init__()
        self._masker = masker or SensitiveDataMasker()

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as a JSON string.

        Args:
            record: Log record to format.

        Returns:
            JSON-encoded log entry.
        """
        message = record.getMessage()
        payload: dict[str, Any] = {
            "timestamp": self._format_timestamp(record),
            "level": record.levelname,
            "logger": record.name,
            "message": self._masker.mask(message),
            CORRELATION_ID_FIELD: getattr(record, CORRELATION_ID_FIELD, resolve_correlation_id()),
        }

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        for key, value in record.__dict__.items():
            if key in _STANDARD_RECORD_FIELDS or key.startswith("_"):
                continue
            if isinstance(value, (str, int, float, bool, type(None))):
                payload[key] = value

        return json.dumps(payload, ensure_ascii=False)

    @staticmethod
    def _format_timestamp(record: logging.LogRecord) -> str:
        """Return an ISO-8601 UTC timestamp for the log record."""
        created = datetime.fromtimestamp(record.created, tz=UTC)
        return created.isoformat(timespec="milliseconds")
