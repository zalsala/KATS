"""Shared fixtures for KIS REST client tests."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any

from app.broker.kis.auth.authentication_client import AuthenticationClient
from app.broker.kis.auth.header_builder import HeaderBuilder
from app.broker.kis.auth.token_cache import TokenCache
from app.broker.kis.auth.token_manager import TokenManager
from app.broker.kis.rest.http_transport import RestHttpResponse
from app.broker.kis.rest.kis_rest_client import build_kis_rest_client
from app.config.config_models import BrokerConfig, RetryConfig, TimeoutConfig
from tests.fixtures.auth_fixtures import MockHttpTransport, make_auth_config


@dataclass
class MockRestHttpTransport:
    """Configurable REST transport for tests."""

    responses: deque[RestHttpResponse | Exception] = field(default_factory=deque)
    default_response: RestHttpResponse | None = None
    calls: list[dict[str, Any]] = field(default_factory=list)

    def queue(self, *items: RestHttpResponse | Exception) -> None:
        """Queue responses or exceptions for subsequent requests."""
        self.responses.extend(items)

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        body: dict[str, Any] | None = None,
        timeout_seconds: float,
    ) -> RestHttpResponse:
        """Return the next queued response or the default response."""
        self.calls.append(
            {
                "method": method,
                "url": url,
                "headers": headers,
                "body": body,
                "timeout_seconds": timeout_seconds,
            }
        )
        if self.responses:
            item = self.responses.popleft()
            if isinstance(item, Exception):
                raise item
            return item
        if self.default_response is not None:
            return self.default_response
        return _success_response()

    @property
    def call_count(self) -> int:
        """Return the number of executed requests."""
        return len(self.calls)


def _success_response(
    *,
    output: dict[str, Any] | None = None,
    status_code: int = 200,
) -> RestHttpResponse:
    body: dict[str, Any] = {
        "rt_cd": "0",
        "msg_cd": "MCA00000",
        "msg1": "정상처리 되었습니다.",
    }
    if output is not None:
        body["output"] = output
    return RestHttpResponse(status_code=status_code, body=body, text=str(body), headers={})


def _error_response(
    *,
    status_code: int = 200,
    rt_cd: str = "1",
    msg_cd: str = "ERROR",
    msg1: str = "error",
) -> RestHttpResponse:
    body = {"rt_cd": rt_cd, "msg_cd": msg_cd, "msg1": msg1}
    return RestHttpResponse(status_code=status_code, body=body, text=str(body), headers={})


def build_test_rest_client(
    tmp_path: object,
    transport: MockRestHttpTransport,
    *,
    max_retry: int = 3,
    backoff_factor: int = 2,
    timeout_seconds: int = 10,
    is_vts: bool = True,
) -> tuple[object, MockRestHttpTransport]:
    """Build a REST client wired with mock auth and transport."""
    from pathlib import Path

    assert isinstance(tmp_path, Path)
    auth_config = make_auth_config()
    auth_transport = MockHttpTransport()
    auth_client = AuthenticationClient(
        base_url="https://openapivts.koreainvestment.com:29443",
        transport=auth_transport,
    )
    token_cache = TokenCache(token_path=tmp_path / "token.json")
    token_manager = TokenManager(
        auth_config=auth_config,
        auth_client=auth_client,
        token_cache=token_cache,
    )
    token_manager.issue()
    header_builder = HeaderBuilder(
        app_key=auth_config.app_key,
        app_secret=auth_config.app_secret,
    )
    broker_config = BrokerConfig(
        base_url="https://openapivts.koreainvestment.com:29443",
        websocket_url="ws://ops.koreainvestment.com:31000",
        timeout=TimeoutConfig(connect=timeout_seconds, read=timeout_seconds, write=timeout_seconds),
        retry=RetryConfig(max_retry=max_retry, backoff_factor=backoff_factor),
    )
    client = build_kis_rest_client(
        broker_config=broker_config,
        token_manager=token_manager,
        header_builder=header_builder,
        transport=transport,
        is_vts=is_vts,
    )
    return client, transport
