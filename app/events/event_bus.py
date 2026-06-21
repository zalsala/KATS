"""EventBus interface."""

from __future__ import annotations

from typing import Protocol

from app.events.base_event import BaseEvent
from app.events.dead_letter_queue import DeadLetterQueue
from app.events.event_handler import EventHandler
from app.events.event_types import EventType


class EventBus(Protocol):
    """Event bus publish/subscribe interface."""

    def publish(self, event: BaseEvent) -> None:
        """Publish an event to all subscribers."""
        ...

    def subscribe(self, event_type: EventType, handler: EventHandler) -> str:
        """Subscribe a handler and return subscription ID."""
        ...

    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe by subscription ID."""
        ...

    @property
    def dead_letter_queue(self) -> DeadLetterQueue:
        """Return the dead letter queue."""
        ...
