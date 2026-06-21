"""In-memory thread-safe EventBus implementation."""

from __future__ import annotations

import logging
import threading
from collections import defaultdict

from app.events.base_event import BaseEvent
from app.events.dead_letter_queue import DeadLetterQueue
from app.events.event_handler import EventHandler
from app.events.event_subscriber import EventSubscriber
from app.events.event_types import EventType

logger = logging.getLogger(__name__)


class InMemoryEventBus:
    """Thread-safe in-memory EventBus with dead letter support."""

    def __init__(self, *, dead_letter_queue: DeadLetterQueue | None = None) -> None:
        self._lock = threading.RLock()
        self._subscribers: dict[EventType, list[EventSubscriber]] = defaultdict(list)
        self._by_id: dict[str, EventSubscriber] = {}
        self._dlq = dead_letter_queue or DeadLetterQueue()

    @property
    def dead_letter_queue(self) -> DeadLetterQueue:
        return self._dlq

    def publish(self, event: BaseEvent) -> None:
        """Publish an event to all handlers for its type."""
        with self._lock:
            subscribers = tuple(self._subscribers.get(event.event_type, ()))

        for subscriber in subscribers:
            try:
                subscriber.handler(event)
            except Exception as exc:
                logger.exception(
                    "Event handler failed event=%s handler=%s",
                    event.event_name,
                    subscriber.handler_name,
                )
                self._dlq.push(
                    event,
                    handler_name=subscriber.handler_name,
                    error=str(exc),
                )

    def subscribe(self, event_type: EventType, handler: EventHandler) -> str:
        """Subscribe a handler to an event type."""
        subscriber = EventSubscriber.create(event_type=event_type, handler=handler)
        with self._lock:
            self._subscribers[event_type].append(subscriber)
            self._by_id[subscriber.subscription_id] = subscriber
        logger.info(
            "Subscribed handler=%s event_type=%s id=%s",
            subscriber.handler_name,
            event_type.value,
            subscriber.subscription_id,
        )
        return subscriber.subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Remove a subscription by ID."""
        with self._lock:
            subscriber = self._by_id.pop(subscription_id, None)
            if subscriber is None:
                return False
            handlers = self._subscribers.get(subscriber.event_type, [])
            self._subscribers[subscriber.event_type] = [
                item for item in handlers if item.subscription_id != subscription_id
            ]
        logger.info("Unsubscribed id=%s", subscription_id)
        return True

    def subscriber_count(self, event_type: EventType) -> int:
        """Return active subscriber count for an event type."""
        with self._lock:
            return len(self._subscribers.get(event_type, []))
