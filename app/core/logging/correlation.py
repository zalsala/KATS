"""Correlation ID context management for distributed log tracing."""

from __future__ import annotations

import uuid
from contextvars import ContextVar, Token
from typing import Final

CORRELATION_ID_PREFIX: Final[str] = "kats"
UNKNOWN_CORRELATION_ID: Final[str] = "-"

_correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def generate_correlation_id() -> str:
    """Generate a new correlation ID for tracing a request flow.

    Returns:
        Unique correlation identifier prefixed with ``kats-``.
    """
    return f"{CORRELATION_ID_PREFIX}-{uuid.uuid4().hex[:16]}"


def get_correlation_id() -> str | None:
    """Return the correlation ID for the current execution context."""
    return _correlation_id.get()


def set_correlation_id(correlation_id: str) -> Token[str | None]:
    """Set the correlation ID for the current execution context.

    Args:
        correlation_id: Correlation identifier to bind.

    Returns:
        Context token for restoring the previous value.
    """
    return _correlation_id.set(correlation_id)


def reset_correlation_id(token: Token[str | None]) -> None:
    """Restore the previous correlation ID using a context token.

    Args:
        token: Token returned by ``set_correlation_id``.
    """
    _correlation_id.reset(token)


def resolve_correlation_id() -> str:
    """Return the active correlation ID or a placeholder when unset."""
    return get_correlation_id() or UNKNOWN_CORRELATION_ID


class CorrelationContext:
    """Context manager that binds a correlation ID for a code block.

    Example:
        with CorrelationContext() as cid:
            logger.info("Processing order")
    """

    def __init__(self, correlation_id: str | None = None) -> None:
        """Initialize the context manager.

        Args:
            correlation_id: Explicit ID to use. A new ID is generated when omitted.
        """
        self._correlation_id = correlation_id or generate_correlation_id()
        self._token: Token[str | None] | None = None

    @property
    def correlation_id(self) -> str:
        """Return the bound correlation ID."""
        return self._correlation_id

    def __enter__(self) -> str:
        """Bind the correlation ID and return it."""
        self._token = set_correlation_id(self._correlation_id)
        return self._correlation_id

    def __exit__(self, *_args: object) -> None:
        """Restore the previous correlation ID."""
        if self._token is not None:
            reset_correlation_id(self._token)
