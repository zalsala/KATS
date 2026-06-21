"""KisWebSocketClient tests."""

from __future__ import annotations

import json

import pytest
from tests.fixtures.ws_fixtures import (
    build_test_websocket_service,
    sample_price_pipe_message,
)

from app.broker.kis.websocket.exceptions import WebSocketConnectionError

pytestmark = pytest.mark.unit


class TestKisWebSocketClient:
    """Mock WebSocket tests for KisWebSocketClient."""

    def test_connect_uses_approval_key_manager(self, tmp_path) -> None:
        service, transport, _ = build_test_websocket_service(tmp_path)

        service.connect()

        assert transport.is_open is True
        assert transport.connect_calls[0][0] == "ws://ops.koreainvestment.com:31000"
        assert transport.connect_calls[0][1]["approval_key"] == "mock-approval-key"

    def test_subscribe_sends_registry_tr_id(self, tmp_path) -> None:
        service, transport, _ = build_test_websocket_service(tmp_path)
        service.connect()

        service.subscribe_price("005930")

        payload = json.loads(transport.sent[0])
        assert payload["body"]["input"]["tr_id"] == "H0STCNT0"
        assert payload["body"]["input"]["tr_key"] == "005930"

    def test_receive_parses_price_message(self, tmp_path) -> None:
        service, _, _ = build_test_websocket_service(
            tmp_path,
            incoming_messages=[sample_price_pipe_message()],
        )
        service.connect()
        service.subscribe_price("005930")

        entity = service.receive()

        assert entity is not None
        assert entity.symbol_code == "005930"
        assert entity.price == "70000"

    def test_reconnect_resubscribes(self, tmp_path) -> None:
        service, transport, client = build_test_websocket_service(tmp_path)
        service.connect()
        service.subscribe_price("005930")
        transport.close()

        service.reconnect()

        assert transport.is_open is True
        assert len(transport.sent) >= 2
        assert len(client.subscription_manager.all_subscriptions()) == 1

    def test_connect_failure_raises(self, tmp_path) -> None:
        from tests.fixtures.auth_fixtures import (
            MockHttpTransport,
            make_kats_config,
            make_kis_secrets,
        )
        from tests.fixtures.ws_fixtures import MockWsTransport

        from app.broker.kis.auth import build_authentication_components
        from app.broker.kis.websocket.kis_ws_client import KisWebSocketClient
        from app.config.app_settings import AppSettings

        config = make_kats_config()
        settings = AppSettings.create(tmp_path, config, make_kis_secrets())
        auth = build_authentication_components(settings, transport=MockHttpTransport())
        auth.token_manager.issue()
        auth.approval_key_manager.issue()
        transport = MockWsTransport(fail_connect=True)
        client = KisWebSocketClient(
            websocket_url=settings.kis_websocket_url,
            transport=transport,
            approval_key_manager=auth.approval_key_manager,
            header_builder=auth.header_builder,
        )

        with pytest.raises(WebSocketConnectionError):
            client.connect()
