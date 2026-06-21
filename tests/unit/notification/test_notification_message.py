"""NotificationMessage tests."""

from __future__ import annotations

import pytest

from app.notification.notification_category import NotificationCategory
from app.notification.notification_message import NotificationMessage

pytestmark = pytest.mark.unit


def test_notification_message_masks_sensitive_account_number() -> None:
    message = NotificationMessage(
        category=NotificationCategory.ORDER_SUCCESS,
        title="주문 성공",
        body="account_no=123456789012 accepted",
        context={"account_no": "123456789012"},
    )
    masked = message.masked()
    assert "123456789012" not in masked.body
    assert masked.context["account_no"] == "****"


def test_notification_message_to_dict_contains_category() -> None:
    message = NotificationMessage(
        category=NotificationCategory.EXECUTION,
        title="체결",
        body="filled",
    )
    payload = message.to_dict()
    assert payload["category"] == "execution"
    assert payload["title"] == "체결"
