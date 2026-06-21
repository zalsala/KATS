"""Notification application service."""

from __future__ import annotations

import logging
from typing import Any

from app.core.logging import CorrelationContext, LogCategory, get_logger
from app.database.database_manager import DatabaseManager
from app.events.event_bus_service import EventBusService
from app.notification.in_memory_notification_store import InMemoryNotificationStore
from app.notification.notification_event_handler import NotificationEventHandler
from app.notification.notification_manager import NotificationManager
from app.notification.notification_message import NotificationMessage
from app.notification.providers.console_notification_provider import ConsoleNotificationProvider
from app.notification.providers.plugin_notification_provider import PluginNotificationProvider
from app.notification.providers.ui_notification_provider import UiNotificationProvider
from app.plugins.notification_registry import NotificationRegistry
from app.repository.interfaces.notification_repository import NotificationRepository


def _resolve_logger() -> logging.Logger:
    try:
        return get_logger(__name__, category=LogCategory.SYSTEM)
    except RuntimeError:
        return logging.getLogger(__name__)


class NotificationService:
    """External entry point for user notifications."""

    def __init__(
        self,
        *,
        manager: NotificationManager | None = None,
        event_handler: NotificationEventHandler | None = None,
        event_bus: EventBusService | None = None,
        store: InMemoryNotificationStore | None = None,
        notification_registry: NotificationRegistry | None = None,
        notification_repository: NotificationRepository | None = None,
        enable_console: bool = True,
        enable_ui: bool = True,
        enable_plugins: bool = True,
    ) -> None:
        self._store = store or InMemoryNotificationStore()
        self._manager = manager or NotificationManager(store=self._store)
        self._event_bus = event_bus
        self._handler = event_handler or NotificationEventHandler(manager=self._manager)
        self._notification_repository = notification_repository
        self._logger = _resolve_logger()
        self._started = False

        if enable_console and not self._manager.has_provider(ConsoleNotificationProvider):
            self._manager.register_provider(ConsoleNotificationProvider())
        if enable_ui:
            self._manager.register_provider(UiNotificationProvider(event_bus=event_bus))
        if enable_plugins and notification_registry is not None:
            self._manager.register_provider(
                PluginNotificationProvider(registry=notification_registry)
            )

    @property
    def manager(self) -> NotificationManager:
        return self._manager

    @property
    def store(self) -> InMemoryNotificationStore:
        return self._store

    @property
    def event_handler(self) -> NotificationEventHandler:
        return self._handler

    @property
    def event_bus(self) -> EventBusService | None:
        return self._event_bus

    def start(self, event_bus: EventBusService | None = None) -> None:
        """Register notification handlers with EventBus."""
        bus = event_bus or self._event_bus
        if bus is None:
            msg = "EventBusService is required to start notification subscriptions"
            raise ValueError(msg)
        self._ensure_ui_provider(bus)
        self._handler.register(bus)
        self._started = True
        self._logger.info("NotificationService started with EventBus subscriptions")

    def stop(self, event_bus: EventBusService | None = None) -> None:
        """Unregister notification handlers from EventBus."""
        bus = event_bus or self._event_bus
        if bus is not None and self._started:
            self._handler.unregister(bus)
            self._started = False

    def notify(self, message: NotificationMessage) -> dict[str, Any]:
        """Send a notification directly through the manager."""
        with CorrelationContext():
            result = self._manager.notify(message)
            if self._notification_repository is not None:
                self._notification_repository.save(message.masked())
            return result

    def list_notifications(self) -> list[dict[str, Any]]:
        """Return stored notification summaries."""
        return [message.to_dict() for message in self._store.list_all()]

    def _ensure_ui_provider(self, event_bus: EventBusService) -> None:
        for provider in self._manager.providers:
            if isinstance(provider, UiNotificationProvider):
                provider.bind_event_bus(event_bus)
                return
        self._manager.register_provider(UiNotificationProvider(event_bus=event_bus))


def build_notification_service(
    *,
    event_bus: EventBusService | None = None,
    notification_registry: NotificationRegistry | None = None,
    notification_repository: NotificationRepository | None = None,
    database_manager: DatabaseManager | None = None,
    enable_console: bool = True,
    enable_ui: bool = True,
    enable_plugins: bool = True,
) -> NotificationService:
    """Create a NotificationService wired with default providers."""
    repository = notification_repository
    if repository is None and database_manager is not None:
        database_manager.initialize()
        repository = database_manager.build_notification_repository()
    return NotificationService(
        event_bus=event_bus,
        notification_registry=notification_registry,
        notification_repository=repository,
        enable_console=enable_console,
        enable_ui=enable_ui,
        enable_plugins=enable_plugins,
    )
