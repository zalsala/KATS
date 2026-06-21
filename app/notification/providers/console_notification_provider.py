"""Console notification provider."""

from __future__ import annotations

import logging

from app.notification.notification_channel import NotificationChannel
from app.notification.notification_message import NotificationMessage


class ConsoleNotificationProvider:
    """Write notifications to the application logger."""

    def __init__(self, *, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger("kats.notification.console")

    @property
    def channel(self) -> NotificationChannel:
        return NotificationChannel.CONSOLE

    def send(self, message: NotificationMessage) -> bool:
        log_method = {
            "ERROR": self._logger.error,
            "WARN": self._logger.warning,
            "WARNING": self._logger.warning,
        }.get(message.level.upper(), self._logger.info)
        log_method("[%s] %s: %s", message.category, message.title, message.body)
        return True
