"""Notification failure isolation tests."""

from __future__ import annotations

import pytest

from app.notification.notification_category import NotificationCategory
from app.notification.notification_channel import NotificationChannel
from app.notification.notification_manager import NotificationManager
from app.notification.notification_message import NotificationMessage
from app.notification.providers.console_notification_provider import ConsoleNotificationProvider


class FailingProvider:
    @property
    def channel(self) -> NotificationChannel:
        return NotificationChannel.PLUGIN

    def send(self, message: NotificationMessage) -> bool:
        raise RuntimeError("provider failed")


pytestmark = pytest.mark.unit


def test_manager_continues_after_provider_failure() -> None:
    manager = NotificationManager(
        providers=[FailingProvider(), ConsoleNotificationProvider()],
    )
    result = manager.notify(
        NotificationMessage(
            category=NotificationCategory.SYSTEM_ERROR,
            title="시스템 오류",
            body="test",
            level="ERROR",
        )
    )
    assert result["channels"]["plugin"] is False
    assert result["channels"]["console"] is True
    assert len(manager.store.list_all()) == 1
