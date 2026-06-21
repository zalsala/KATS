"""SubscriptionManager tests."""

from __future__ import annotations

import json

import pytest

from app.broker.kis.websocket.subscription_manager import SubscriptionManager
from app.dto.websocket.subscribe_request import SubscribeRequest

pytestmark = pytest.mark.unit


class TestSubscriptionManager:
    """Tests for WebSocket SubscriptionManager."""

    def test_build_subscribe_payload(self) -> None:
        manager = SubscriptionManager()
        request = SubscribeRequest.for_price("005930")

        payload = json.loads(manager.build_payload("approval-key", request))

        assert payload["header"]["approval_key"] == "approval-key"
        assert payload["header"]["tr_type"] == "1"
        assert payload["body"]["input"]["tr_id"] == "H0STCNT0"
        assert payload["body"]["input"]["tr_key"] == "005930"

    def test_register_and_resubscribe(self) -> None:
        manager = SubscriptionManager()
        manager.register(SubscribeRequest.for_price("005930"))
        manager.register(SubscribeRequest.for_orderbook("005930"))

        assert len(manager.all_subscriptions()) == 2

    def test_unregister_removes_subscription(self) -> None:
        manager = SubscriptionManager()
        manager.register(SubscribeRequest.for_price("005930"))
        manager.register(SubscribeRequest.for_price("005930", action="unsubscribe"))

        assert manager.all_subscriptions() == ()
