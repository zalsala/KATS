"""Shared fixtures for WebSocket tests."""

from __future__ import annotations

from pathlib import Path

from app.broker.kis.auth import build_authentication_components
from app.broker.kis.websocket.kis_ws_client import KisWebSocketClient
from app.broker.kis.websocket.reconnect_manager import ReconnectManager
from app.broker.kis.websocket.subscription_manager import SubscriptionManager
from app.config.app_settings import AppSettings
from app.service.websocket.websocket_service import WebSocketService
from tests.fixtures.auth_fixtures import MockHttpTransport, make_kats_config, make_kis_secrets


class MockWsTransport:
    """Mock WebSocket transport for unit tests."""

    def __init__(
        self,
        *,
        incoming_messages: list[str] | None = None,
        fail_connect: bool = False,
    ) -> None:
        self._incoming = list(incoming_messages or [])
        self._fail_connect = fail_connect
        self._open = False
        self.sent: list[str] = []
        self.connect_calls: list[tuple[str, dict[str, str]]] = []
        self.closed = False

    @property
    def is_open(self) -> bool:
        return self._open

    def connect(self, url: str, headers: dict[str, str]) -> None:
        if self._fail_connect:
            msg = "connection refused"
            raise ConnectionError(msg)
        self.connect_calls.append((url, headers))
        self._open = True

    def send(self, message: str) -> None:
        self.sent.append(message)

    def receive(self, timeout: float | None = None) -> str | None:
        _ = timeout
        if not self._incoming:
            return None
        return self._incoming.pop(0)

    def close(self) -> None:
        self._open = False
        self.closed = True

    def push(self, message: str) -> None:
        """Queue an incoming message."""
        self._incoming.append(message)


def sample_price_pipe_message() -> str:
    return "0|H0STCNT0|002|005930^154208^70000^2^500^1000"


def sample_orderbook_pipe_message() -> str:
    return "0|H0STASP0|002|005930^70100^10^70000^20"


def sample_execution_pipe_message() -> str:
    return "0|H0STCNI0|002|12345678^0000123456^005930^02^1^70000"


def build_test_websocket_service(
    tmp_path: Path,
    *,
    incoming_messages: list[str] | None = None,
    websocket_url: str = "ws://ops.koreainvestment.com:31000",
) -> tuple[WebSocketService, MockWsTransport, KisWebSocketClient]:
    """Build WebSocketService with mock transport and auth components."""
    transport = MockWsTransport(incoming_messages=incoming_messages)
    config = make_kats_config()
    config.broker.websocket_url = websocket_url
    settings = AppSettings.create(tmp_path, config, make_kis_secrets())
    http_transport = MockHttpTransport()
    auth = build_authentication_components(settings, transport=http_transport)
    auth.token_manager.issue()
    auth.approval_key_manager.issue()

    sleep_log: list[float] = []

    def _sleep(delay: float) -> None:
        sleep_log.append(delay)

    reconnect = ReconnectManager(max_attempts=3, base_delay_seconds=0.01, sleep_func=_sleep)
    client = KisWebSocketClient(
        websocket_url=settings.kis_websocket_url,
        transport=transport,
        approval_key_manager=auth.approval_key_manager,
        header_builder=auth.header_builder,
        subscription_manager=SubscriptionManager(),
        reconnect_manager=reconnect,
        receive_timeout=1.0,
    )
    service = WebSocketService(ws_client=client)
    return service, transport, client
