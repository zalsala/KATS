"""Notification registry for plugin-backed notifications."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.plugins.base_notification import BaseNotification

NotificationFactory = Callable[..., BaseNotification]


class NotificationRegistry:
    """Maps notification channel names to plugin notification factories."""

    def __init__(self) -> None:
        self._factories: dict[str, NotificationFactory] = {}

    def register(self, channel_name: str, factory: NotificationFactory) -> None:
        """Register a notification factory by channel name."""
        self._factories[channel_name] = factory

    def create(self, channel_name: str, **parameters: Any) -> BaseNotification:
        """Instantiate a notification plugin from a registered channel."""
        factory = self._factories.get(channel_name)
        if factory is None:
            msg = f"Unknown notification channel: {channel_name}"
            raise ValueError(msg)
        return factory(**parameters)

    def send(
        self,
        channel_name: str,
        message: str,
        *,
        context: dict[str, Any] | None = None,
        **parameters: Any,
    ) -> bool:
        """Send a message through a registered notification plugin."""
        notifier = self.create(channel_name, **parameters)
        return notifier.send(message, context=context)

    def list_channels(self) -> tuple[str, ...]:
        """Return registered notification channel names."""
        return tuple(sorted(self._factories))

    def is_registered(self, channel_name: str) -> bool:
        """Return whether a channel name is registered."""
        return channel_name in self._factories
