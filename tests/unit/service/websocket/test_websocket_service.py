"""WebSocketService tests."""

from __future__ import annotations

import pytest
from tests.fixtures.ws_fixtures import (
    build_test_websocket_service,
    sample_execution_pipe_message,
    sample_orderbook_pipe_message,
    sample_price_pipe_message,
)

from app.domain.realtime.entities import ExecutionNotice, RealtimeOrderbook, RealtimePrice

pytestmark = pytest.mark.unit


class TestWebSocketService:
    """Tests for WebSocketService entry point."""

    def test_subscribe_and_receive_price(self, tmp_path) -> None:
        service, _, _ = build_test_websocket_service(
            tmp_path,
            incoming_messages=[sample_price_pipe_message()],
        )
        service.connect()
        service.subscribe_price("005930")

        entity = service.receive()

        assert isinstance(entity, RealtimePrice)
        assert entity.price == "70000"

    def test_subscribe_and_receive_orderbook(self, tmp_path) -> None:
        service, _, _ = build_test_websocket_service(
            tmp_path,
            incoming_messages=[sample_orderbook_pipe_message()],
        )
        service.connect()
        service.subscribe_orderbook("005930")

        entity = service.receive()

        assert isinstance(entity, RealtimeOrderbook)
        assert entity.ask_price == "70100"

    def test_subscribe_and_receive_execution_notice(self, tmp_path) -> None:
        service, _, _ = build_test_websocket_service(
            tmp_path,
            incoming_messages=[sample_execution_pipe_message()],
        )
        service.connect()
        service.subscribe_execution_notice("user01")

        entity = service.receive()

        assert isinstance(entity, ExecutionNotice)
        assert entity.order_number == "0000123456"

    def test_disconnect_closes_transport(self, tmp_path) -> None:
        service, transport, _ = build_test_websocket_service(tmp_path)
        service.connect()

        service.disconnect()

        assert transport.closed is True
        assert service.is_connected is False
