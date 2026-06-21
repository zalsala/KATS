"""UiNotificationProvider tests."""

from __future__ import annotations

import pytest
from tests.fixtures.notification_fixtures import build_test_event_bus_service

from app.events.event_types import EventType
from app.notification.notification_category import NotificationCategory
from app.notification.notification_message import NotificationMessage
from app.notification.providers.ui_notification_provider import UiNotificationProvider

pytestmark = pytest.mark.unit


def test_ui_provider_publishes_system_event() -> None:
    event_bus = build_test_event_bus_service()
    captured: list[str] = []

    def _capture(event: object) -> None:
        captured.append(getattr(event, "event_name", ""))

    event_bus.subscribe(EventType.SYSTEM, _capture)
    provider = UiNotificationProvider(event_bus=event_bus)
    message = NotificationMessage(
        category=NotificationCategory.SYSTEM_ERROR,
        title="시스템 오류",
        body="unexpected failure",
        level="ERROR",
    )
    assert provider.send(message) is True
    assert "notification.created" in captured
