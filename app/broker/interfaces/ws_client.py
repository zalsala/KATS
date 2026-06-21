"""WebSocket client interface."""

from __future__ import annotations

from typing import Protocol

from app.dto.websocket.subscribe_request import SubscribeRequest
from app.dto.websocket.ws_messages import (
    ExecutionNoticeMessage,
    RealtimeOrderbookMessage,
    RealtimePriceMessage,
)

ParsedMessage = RealtimePriceMessage | RealtimeOrderbookMessage | ExecutionNoticeMessage


class WebSocketClient(Protocol):
    """Broker WebSocket client interface."""

    @property
    def is_connected(self) -> bool:
        """Return True when connected."""
        ...

    def connect(self) -> None:
        """Open WebSocket connection using ApprovalKeyManager."""
        ...

    def disconnect(self) -> None:
        """Close WebSocket connection."""
        ...

    def subscribe(self, request: SubscribeRequest) -> None:
        """Subscribe to a realtime channel."""
        ...

    def unsubscribe(self, request: SubscribeRequest) -> None:
        """Unsubscribe from a realtime channel."""
        ...

    def receive(self, timeout: float | None = None) -> ParsedMessage | None:
        """Receive and parse the next message."""
        ...

    def reconnect(self) -> None:
        """Reconnect and restore subscriptions."""
        ...
