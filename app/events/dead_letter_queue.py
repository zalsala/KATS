"""Dead letter queue for failed event handlers."""

from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime

from app.events.base_event import BaseEvent


@dataclass(frozen=True, slots=True)
class DeadLetterEntry:
    """Failed event handler record."""

    event: BaseEvent
    handler_name: str
    error: str
    failed_at: datetime


class DeadLetterQueue:
    """Thread-safe in-memory dead letter queue."""

    def __init__(self, *, max_size: int = 1000) -> None:
        self._entries: deque[DeadLetterEntry] = deque(maxlen=max_size)
        self._lock = threading.Lock()

    def push(self, event: BaseEvent, *, handler_name: str, error: str) -> None:
        """Store a failed event for later inspection."""
        entry = DeadLetterEntry(
            event=event,
            handler_name=handler_name,
            error=error,
            failed_at=datetime.now(UTC),
        )
        with self._lock:
            self._entries.append(entry)

    def all(self) -> tuple[DeadLetterEntry, ...]:
        """Return all dead letter entries."""
        with self._lock:
            return tuple(self._entries)

    def clear(self) -> None:
        """Remove all dead letter entries."""
        with self._lock:
            self._entries.clear()

    def size(self) -> int:
        """Return current queue size."""
        with self._lock:
            return len(self._entries)
