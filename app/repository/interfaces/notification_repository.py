"""Notification persistence repository interface."""

from __future__ import annotations

from typing import Protocol

from app.notification.notification_message import NotificationMessage


class NotificationRepository(Protocol):
    """Persistence contract for notification history."""

    def save(self, message: NotificationMessage) -> None:
        """Persist a notification message."""

    def get(self, notification_id: str) -> NotificationMessage | None:
        """Load a notification by id."""

    def list_all(self, *, limit: int = 500) -> list[NotificationMessage]:
        """Return stored notifications."""
