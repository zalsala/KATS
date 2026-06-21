"""In-memory notification history store."""

from __future__ import annotations

from collections import deque

from app.notification.notification_message import NotificationMessage


class InMemoryNotificationStore:
    """Stores recent notifications for inspection and UI replay."""

    def __init__(self, *, max_entries: int = 500) -> None:
        self._max_entries = max_entries
        self._entries: deque[NotificationMessage] = deque(maxlen=max_entries)

    def save(self, message: NotificationMessage) -> None:
        """Persist a notification message."""
        self._entries.append(message)

    def list_all(self) -> tuple[NotificationMessage, ...]:
        """Return stored notifications in insertion order."""
        return tuple(self._entries)

    def get(self, notification_id: str) -> NotificationMessage | None:
        """Return a notification by id."""
        for entry in self._entries:
            if entry.notification_id == notification_id:
                return entry
        return None

    def clear(self) -> None:
        """Remove all stored notifications."""
        self._entries.clear()
