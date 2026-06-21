"""Notification plugin adapter."""

from __future__ import annotations

from app.plugins.notification_registry import NotificationRegistry
from app.plugins.plugin_registry import LoadedPlugin


class NotificationPluginAdapter:
    """Register external notification plugins with NotificationRegistry."""

    def adapt(self, plugin: LoadedPlugin, notification_registry: NotificationRegistry) -> str:
        """Register a loaded notification plugin factory."""
        channel_name = plugin.manifest.resolve_registration_key()
        notification_registry.register(channel_name, plugin.plugin_class)
        return channel_name
