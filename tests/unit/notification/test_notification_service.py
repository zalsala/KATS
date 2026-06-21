"""NotificationService tests."""

from __future__ import annotations

import pytest
from tests.fixtures.notification_fixtures import build_test_notification_service

from app.notification.notification_category import NotificationCategory
from app.notification.notification_message import NotificationMessage
from app.notification.providers.console_notification_provider import ConsoleNotificationProvider
from app.service.notification.notification_service import (
    NotificationService,
    build_notification_service,
)

pytestmark = pytest.mark.unit


def test_notification_service_notify_stores_message() -> None:
    service = build_test_notification_service(enable_ui=False, enable_plugins=False)
    service.notify(
        NotificationMessage(
            category=NotificationCategory.STRATEGY_STARTED,
            title="전략 시작",
            body="template started",
        )
    )
    notifications = service.list_notifications()
    assert len(notifications) == 1
    assert notifications[0]["category"] == NotificationCategory.STRATEGY_STARTED


def test_notification_service_start_requires_event_bus() -> None:
    service = NotificationService(enable_console=False, enable_ui=False, enable_plugins=False)
    with pytest.raises(ValueError, match="EventBusService"):
        service.start()


def test_build_notification_service_registers_default_providers() -> None:
    service = build_notification_service()
    assert service.manager.has_provider(ConsoleNotificationProvider)
    assert len(service.manager.providers) >= 1
