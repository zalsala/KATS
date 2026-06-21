"""Notification provider protocol."""

from __future__ import annotations

from typing import Protocol

from app.notification.notification_channel import NotificationChannel
from app.notification.notification_message import NotificationMessage


class NotificationProvider(Protocol):
    """Delivers a notification through a specific channel."""

    @property
    def channel(self) -> NotificationChannel:
        """Return the provider channel."""

    def send(self, message: NotificationMessage) -> bool:
        """Deliver a notification message."""
