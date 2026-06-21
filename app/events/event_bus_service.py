"""EventBus application service."""

from __future__ import annotations

import logging

from app.core.logging import CorrelationContext, LogCategory, get_logger
from app.events.base_event import BaseEvent
from app.events.event_bus import EventBus
from app.events.event_handler import EventHandler
from app.events.event_types import EventType
from app.events.in_memory_event_bus import InMemoryEventBus


def _resolve_logger() -> logging.Logger:
    try:
        return get_logger(__name__, category=LogCategory.SYSTEM)
    except RuntimeError:
        return logging.getLogger(__name__)


class EventBusService:
    """External entry point for publishing and subscribing to events."""

    def __init__(self, *, event_bus: EventBus | None = None) -> None:
        self._bus = event_bus or InMemoryEventBus()
        self._logger = _resolve_logger()

    @property
    def event_bus(self) -> EventBus:
        return self._bus

    def publish(self, event: BaseEvent) -> None:
        """Publish an event with correlation context binding."""
        with CorrelationContext(event.correlation_id):
            self._logger.info(
                "Publishing event name=%s type=%s source=%s correlation_id=%s",
                event.event_name,
                event.event_type.value,
                event.source,
                event.correlation_id,
            )
            self._bus.publish(event)

    def subscribe(self, event_type: EventType, handler: EventHandler) -> str:
        """Subscribe a handler to an event type."""
        subscription_id = self._bus.subscribe(event_type, handler)
        self._logger.info(
            "Handler subscribed type=%s subscription_id=%s",
            event_type.value,
            subscription_id,
        )
        return subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe a handler by subscription ID."""
        removed = self._bus.unsubscribe(subscription_id)
        if removed:
            self._logger.info("Handler unsubscribed subscription_id=%s", subscription_id)
        return removed


def build_event_bus_service(*, event_bus: EventBus | None = None) -> EventBusService:
    """Create an EventBusService with optional custom bus."""
    return EventBusService(event_bus=event_bus)
