"""Injectable WebSocket transport protocol."""

from __future__ import annotations

from typing import Protocol


class WsTransport(Protocol):
    """Low-level WebSocket transport."""

    @property
    def is_open(self) -> bool:
        """Return True when the connection is open."""
        ...

    def connect(self, url: str, headers: dict[str, str]) -> None:
        """Open a WebSocket connection."""
        ...

    def send(self, message: str) -> None:
        """Send a text frame."""
        ...

    def receive(self, timeout: float | None = None) -> str | None:
        """Receive the next text frame, or None on timeout."""
        ...

    def close(self) -> None:
        """Close the connection."""
        ...
