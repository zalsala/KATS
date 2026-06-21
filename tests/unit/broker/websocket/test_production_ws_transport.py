"""Production WebSocket transport tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.broker.kis.websocket.production_ws_transport import (
    ProductionWsTransport,
    build_production_ws_transport,
)

pytestmark = pytest.mark.unit


class FakeWebSocket:
    """In-memory WebSocket connection stub."""

    def __init__(self) -> None:
        self.connected = True
        self.sent: list[str] = []
        self.incoming: list[str] = []
        self.timeout: float | None = None
        self.closed = False

    def send(self, message: str) -> None:
        self.sent.append(message)

    def recv(self) -> str:
        if not self.incoming:
            raise TimeoutError("timed out")
        return self.incoming.pop(0)

    def settimeout(self, timeout: float | None) -> None:
        self.timeout = timeout

    def close(self) -> None:
        self.connected = False
        self.closed = True


class TestProductionWsTransport:
    """Unit tests for ProductionWsTransport."""

    def test_connect_uses_url_from_client(self) -> None:
        fake = FakeWebSocket()
        transport = ProductionWsTransport(connection_factory=lambda *_a, **_k: fake)

        transport.connect("ws://example.test/ws", {"approval_key": "key-1"})

        assert transport.is_open is True

    def test_connect_failure_raises_connection_error(self) -> None:
        def _fail(*_args: object, **_kwargs: object) -> FakeWebSocket:
            msg = "connection refused"
            raise OSError(msg)

        transport = ProductionWsTransport(connection_factory=_fail)

        with pytest.raises(ConnectionError, match="WebSocket connection failed"):
            transport.connect("ws://example.test/ws", {})

        assert transport.is_open is False

    def test_send_transmits_message(self) -> None:
        fake = FakeWebSocket()
        transport = ProductionWsTransport(connection_factory=lambda *_a, **_k: fake)
        transport.connect("ws://example.test/ws", {})

        transport.send('{"hello":"world"}')

        assert fake.sent == ['{"hello":"world"}']

    def test_send_without_connection_raises(self) -> None:
        transport = ProductionWsTransport(connection_factory=lambda *_a, **_k: FakeWebSocket())

        with pytest.raises(ConnectionError, match="not connected"):
            transport.send("ping")

    def test_receive_returns_message(self) -> None:
        fake = FakeWebSocket()
        fake.incoming.append("price-message")
        transport = ProductionWsTransport(connection_factory=lambda *_a, **_k: fake)
        transport.connect("ws://example.test/ws", {})

        message = transport.receive(timeout=1.0)

        assert message == "price-message"
        assert fake.timeout == 1.0

    def test_receive_timeout_returns_none(self) -> None:
        fake = FakeWebSocket()
        transport = ProductionWsTransport(connection_factory=lambda *_a, **_k: fake)
        transport.connect("ws://example.test/ws", {})

        message = transport.receive(timeout=0.5)

        assert message is None

    def test_close_closes_connection(self) -> None:
        fake = FakeWebSocket()
        transport = ProductionWsTransport(connection_factory=lambda *_a, **_k: fake)
        transport.connect("ws://example.test/ws", {})

        transport.close()

        assert fake.closed is True
        assert transport.is_open is False

    def test_build_factory_returns_transport(self) -> None:
        transport = build_production_ws_transport(default_timeout=12.0)

        assert isinstance(transport, ProductionWsTransport)

    @patch("app.broker.kis.websocket.production_ws_transport._create_connection")
    def test_create_connection_delegates_to_websocket_client(
        self,
        mock_create: MagicMock,
    ) -> None:
        fake = FakeWebSocket()
        mock_create.return_value = fake
        transport = build_production_ws_transport()

        transport.connect("ws://ops.koreainvestment.com:31000", {"approval_key": "abc"})

        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args.kwargs
        assert mock_create.call_args.args[0] == "ws://ops.koreainvestment.com:31000"
        assert call_kwargs["header"] == ["approval_key: abc"]
        assert transport.is_open is True
