"""WebSocket TR ID registry integration tests."""

from __future__ import annotations

import pytest

from app.broker.kis.websocket.ws_tr_ids import (
    WS_TR_EXECUTION_NOTICE_MOCK,
    WS_TR_REALTIME_ORDERBOOK,
    WS_TR_REALTIME_PRICE,
)
from app.dto.websocket.subscribe_request import SubscribeRequest

pytestmark = pytest.mark.unit


class TestWebSocketRegistryIntegration:
    """Integration tests for WebSocket TR ID usage."""

    def test_price_subscription_uses_h0stcnt0(self) -> None:
        request = SubscribeRequest.for_price("005930")

        assert request.tr_id == WS_TR_REALTIME_PRICE
        assert request.tr_type == "1"

    def test_orderbook_subscription_uses_h0stasp0(self) -> None:
        request = SubscribeRequest.for_orderbook("005930")

        assert request.tr_id == WS_TR_REALTIME_ORDERBOOK

    def test_execution_subscription_uses_h0stcni0_for_mock(self) -> None:
        request = SubscribeRequest.for_execution_notice("user01", is_mock=True)

        assert request.tr_id == WS_TR_EXECUTION_NOTICE_MOCK
