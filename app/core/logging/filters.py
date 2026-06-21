"""Log record filters for correlation ID and sensitive data masking."""

from __future__ import annotations

import logging

from app.core.logging.constants import CORRELATION_ID_FIELD
from app.core.logging.correlation import resolve_correlation_id
from app.core.logging.masker import SensitiveDataMasker


class CorrelationIdFilter(logging.Filter):
    """Inject the active correlation ID into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add ``correlation_id`` attribute to the log record.

        Args:
            record: Log record to enrich.

        Returns:
            Always True so the record is not suppressed.
        """
        if not hasattr(record, CORRELATION_ID_FIELD):
            setattr(record, CORRELATION_ID_FIELD, resolve_correlation_id())
        return True


class SensitiveDataFilter(logging.Filter):
    """Mask sensitive data in log messages before formatting."""

    def __init__(self, masker: SensitiveDataMasker | None = None) -> None:
        """Initialize the filter.

        Args:
            masker: Optional custom masker instance.
        """
        super().__init__()
        self._masker = masker or SensitiveDataMasker()

    def filter(self, record: logging.LogRecord) -> bool:
        """Mask sensitive content on the log record.

        Args:
            record: Log record to sanitize.

        Returns:
            Always True so the record is not suppressed.
        """
        record.msg = self._masker.mask(str(record.msg))
        if record.args:
            record.args = tuple(
                self._masker.mask(str(arg)) if isinstance(arg, str) else arg for arg in record.args
            )
        return True


class MinimumLevelFilter(logging.Filter):
    """Pass log records at or above a minimum level."""

    def __init__(self, min_level: int) -> None:
        """Initialize the filter.

        Args:
            min_level: Minimum ``logging`` level constant.
        """
        super().__init__()
        self._min_level = min_level

    def filter(self, record: logging.LogRecord) -> bool:
        """Return True when the record meets the minimum level."""
        return record.levelno >= self._min_level
