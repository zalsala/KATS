"""Notification repository tests."""

from __future__ import annotations

import pytest
from tests.fixtures.database_fixtures import build_test_database_manager

from app.notification.notification_category import NotificationCategory
from app.notification.notification_message import NotificationMessage

pytestmark = pytest.mark.unit


def test_notification_repository_save_and_get(tmp_path) -> None:
    manager = build_test_database_manager(tmp_path)
    repository = manager.build_notification_repository()
    message = NotificationMessage(
        notification_id="notif-1",
        category=NotificationCategory.ORDER_SUCCESS,
        title="주문 성공",
        body="accepted",
        context={"account_no": "123456789012"},
    )
    repository.save(message)
    loaded = repository.get("notif-1")
    assert loaded is not None
    assert loaded.title == "주문 성공"
    assert loaded.context["account_no"] == "123456789012"
