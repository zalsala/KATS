"""WebSocket-specific exceptions."""

from __future__ import annotations


class WebSocketError(Exception):
    """Base WebSocket error."""


class WebSocketConnectionError(WebSocketError):
    """Raised when the WebSocket connection fails."""


class WebSocketSubscriptionError(WebSocketError):
    """Raised when subscribe or unsubscribe fails."""


class WebSocketParseError(WebSocketError):
    """Raised when an incoming message cannot be parsed."""
