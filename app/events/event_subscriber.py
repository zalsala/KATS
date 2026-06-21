"""Event subscriber model."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.events.event_handler import EventHandler
from app.events.event_types import EventType


@dataclass(frozen=True, slots=True)
class EventSubscriber:
    """Registered event subscription."""

    subscription_id: str
    event_type: EventType
    handler: EventHandler
    handler_name: str

    @classmethod
    def create(
        cls,
        *,
        event_type: EventType,
        handler: EventHandler,
    ) -> EventSubscriber:
        """Create a subscriber with a generated subscription ID."""
        handler_name = getattr(handler, "__name__", handler.__class__.__name__)
        return cls(
            subscription_id=str(uuid.uuid4()),
            event_type=event_type,
            handler=handler,
            handler_name=handler_name,
        )
