"""Plugin notification provider."""

from __future__ import annotations

import logging

from app.notification.notification_channel import NotificationChannel
from app.notification.notification_message import NotificationMessage
from app.plugins.notification_registry import NotificationRegistry


def _resolve_logger() -> logging.Logger:
    return logging.getLogger(__name__)


class PluginNotificationProvider:
    """Deliver notifications through registered plugin channels."""

    def __init__(
        self,
        *,
        registry: NotificationRegistry,
        channel_names: tuple[str, ...] | None = None,
    ) -> None:
        self._registry = registry
        self._channel_names = channel_names
        self._logger = _resolve_logger()

    @property
    def channel(self) -> NotificationChannel:
        return NotificationChannel.PLUGIN

    def send(self, message: NotificationMessage) -> bool:
        channels = self._channel_names or self._registry.list_channels()
        if not channels:
            return False

        delivered = False
        for channel_name in channels:
            try:
                sent = self._registry.send(
                    channel_name,
                    f"{message.title}: {message.body}",
                    context=message.to_dict(),
                )
                delivered = delivered or sent
            except Exception:  # noqa: BLE001 - plugin failures must not stop app
                self._logger.exception(
                    "Plugin notification failed channel=%s notification_id=%s",
                    channel_name,
                    message.notification_id,
                )
        return delivered
