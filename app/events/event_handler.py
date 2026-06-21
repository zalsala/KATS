"""Event handler protocol."""

from __future__ import annotations

from typing import Protocol

from app.events.base_event import BaseEvent


class EventHandler(Protocol):
    """Callable handler for a single event type."""

    def __call__(self, event: BaseEvent) -> None:
        """Handle the given event."""
        ...
