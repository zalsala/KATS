"""Plugin notification provider integration tests."""

from __future__ import annotations

import pytest
from tests.fixtures.notification_fixtures import build_test_notification_registry
from tests.fixtures.plugins.notifications.console_notifier.notification import ConsoleNotifier

from app.notification.notification_category import NotificationCategory
from app.notification.notification_message import NotificationMessage
from app.notification.providers.plugin_notification_provider import PluginNotificationProvider

pytestmark = pytest.mark.unit


def test_plugin_provider_uses_notification_registry() -> None:
    registry = build_test_notification_registry()
    provider = PluginNotificationProvider(registry=registry)
    message = NotificationMessage(
        category=NotificationCategory.ORDER_SUCCESS,
        title="주문 성공",
        body="accepted",
    )
    assert provider.send(message) is True
    assert ConsoleNotifier.last_message is not None
    assert "주문 성공" in ConsoleNotifier.last_message
