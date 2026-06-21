"""Shared notification test fixtures."""

from __future__ import annotations

from app.events.event_bus_service import EventBusService
from app.events.in_memory_event_bus import InMemoryEventBus
from app.notification.notification_manager import NotificationManager
from app.plugins.notification_registry import NotificationRegistry
from app.service.notification.notification_service import NotificationService
from tests.fixtures.plugins.notifications.console_notifier.notification import ConsoleNotifier


def build_test_event_bus_service() -> EventBusService:
    """Build EventBusService with a fresh in-memory bus."""
    return EventBusService(event_bus=InMemoryEventBus())


def build_test_notification_registry() -> NotificationRegistry:
    """Build registry with the test console notifier plugin."""
    registry = NotificationRegistry()
    registry.register("console", ConsoleNotifier)
    return registry


def build_test_notification_service(
    *,
    notification_registry: NotificationRegistry | None = None,
    enable_console: bool = True,
    enable_ui: bool = True,
    enable_plugins: bool = True,
) -> NotificationService:
    """Build NotificationService for tests."""
    event_bus = build_test_event_bus_service()
    return NotificationService(
        event_bus=event_bus,
        notification_registry=notification_registry or build_test_notification_registry(),
        enable_console=enable_console,
        enable_ui=enable_ui,
        enable_plugins=enable_plugins,
    )


def build_test_notification_manager() -> NotificationManager:
    """Build an empty notification manager."""
    return NotificationManager()
