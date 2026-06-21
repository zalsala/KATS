"""ConsoleNotificationProvider tests."""

from __future__ import annotations

import logging

import pytest

from app.notification.notification_category import NotificationCategory
from app.notification.notification_message import NotificationMessage
from app.notification.providers.console_notification_provider import ConsoleNotificationProvider

pytestmark = pytest.mark.unit


def test_console_provider_logs_notification(caplog: pytest.LogCaptureFixture) -> None:
    provider = ConsoleNotificationProvider(logger=logging.getLogger("test.notification.console"))
    message = NotificationMessage(
        category=NotificationCategory.ORDER_SUCCESS,
        title="주문 성공",
        body="accepted",
        level="INFO",
    )
    with caplog.at_level(logging.INFO, logger="test.notification.console"):
        assert provider.send(message) is True
    assert "주문 성공" in caplog.text
