"""API and operation performance logging utilities."""

from __future__ import annotations

import logging
import time
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from app.core.logging.constants import LATENCY_MS_FIELD, OPERATION_FIELD
from app.core.logging.correlation import resolve_correlation_id


class PerformanceLogger:
    """Measures and logs operation latency for KIS OpenAPI calls."""

    def __init__(self, logger: logging.Logger) -> None:
        """Initialize the performance logger.

        Args:
            logger: Target logger (typically ``kats.api``).
        """
        self._logger = logger

    @contextmanager
    def measure(self, operation: str, **context: Any) -> Generator[None, None, None]:
        """Measure elapsed time for a block and emit a performance log entry.

        Args:
            operation: Operation name (e.g. ``kis.rest.get_balance``).
            **context: Additional structured fields included in the log entry.

        Yields:
            Nothing; used as a context manager.

        Example:
            with perf.measure("kis.rest.place_order", symbol="005930"):
                ...
        """
        start = time.perf_counter()
        error: BaseException | None = None
        try:
            yield
        except BaseException as exc:
            error = exc
            raise
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            self.log_latency(operation, elapsed_ms, error=error, **context)

    def log_latency(
        self,
        operation: str,
        latency_ms: float,
        *,
        error: BaseException | None = None,
        **context: Any,
    ) -> None:
        """Emit a structured performance log entry.

        Args:
            operation: Operation name.
            latency_ms: Elapsed time in milliseconds.
            error: Optional exception when the operation failed.
            **context: Additional structured fields.
        """
        status = "error" if error is not None else "ok"
        extra: dict[str, Any] = {
            OPERATION_FIELD: operation,
            LATENCY_MS_FIELD: round(latency_ms, 3),
            "status": status,
            "correlation_id": resolve_correlation_id(),
            **context,
        }
        message = f"{operation} {status} in {latency_ms:.2f}ms"

        if error is not None:
            self._logger.error(message, extra=extra, exc_info=error)
        else:
            self._logger.info(message, extra=extra)
