"""Shared fixtures for KIS authentication tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from app.broker.kis.auth.http_transport import HttpResponse
from app.config.config_models import AuthenticationConfig, BrokerConfig, KatsConfig
from app.config.secret_manager import KisSecrets


class MockHttpTransport:
    """In-memory HTTP transport for authentication tests."""

    def __init__(
        self,
        *,
        token_response: dict[str, Any] | None = None,
        approval_response: dict[str, Any] | None = None,
        hash_response: dict[str, Any] | None = None,
        status_code: int = 200,
    ) -> None:
        """Initialize mock responses.

        Args:
            token_response: JSON body for token endpoint.
            approval_response: JSON body for approval endpoint.
            hash_response: JSON body for hashkey endpoint.
            status_code: Default HTTP status code.
        """
        self.token_response = token_response or _default_token_response()
        self.approval_response = approval_response or {"approval_key": "mock-approval-key"}
        self.hash_response = hash_response or {"HASH": "mock-hash-key"}
        self.status_code = status_code
        self.calls: list[tuple[str, dict[str, str], dict[str, Any]]] = []
        self.token_call_count = 0

    def post_json(
        self,
        url: str,
        headers: dict[str, str],
        body: dict[str, Any],
    ) -> HttpResponse:
        """Record and return a canned JSON response."""
        self.calls.append((url, headers, body))
        if "/oauth2/tokenP" in url:
            self.token_call_count += 1
            payload = self.token_response
        elif "/oauth2/Approval" in url:
            payload = self.approval_response
        elif "/uapi/hashkey" in url:
            payload = self.hash_response
        else:
            payload = {}
        return HttpResponse(
            status_code=self.status_code,
            body=payload,
            text=str(payload),
        )


def _default_token_response() -> dict[str, str]:
    expires_at = (datetime.now(UTC) + timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S")
    return {
        "access_token": "mock-access-token",
        "access_token_token_expired": expires_at,
        "token_type": "Bearer",
        "expires_in": "43200",
    }


def make_auth_config(
    *,
    app_key: str = "test-app-key",
    app_secret: str = "test-app-secret",
    auto_refresh: bool = True,
    refresh_margin_seconds: int = 300,
    approval_cache_seconds: int = 3600,
    token_path: str = "data/auth/token.json",
) -> AuthenticationConfig:
    """Build an authentication config for tests."""
    return AuthenticationConfig(
        app_key=app_key,
        app_secret=app_secret,
        account_no="12345678",
        account_type="mock",
        token_path=token_path,
        auto_refresh=auto_refresh,
        refresh_margin_seconds=refresh_margin_seconds,
        approval_cache_seconds=approval_cache_seconds,
    )


def make_kats_config(auth_config: AuthenticationConfig | None = None) -> KatsConfig:
    """Build a minimal KatsConfig for auth tests."""
    return KatsConfig(
        broker=BrokerConfig(
            base_url="https://openapivts.koreainvestment.com:29443",
            websocket_url="ws://ops.koreainvestment.com:31000",
        ),
        authentication=auth_config or make_auth_config(),
        environment="development",
    )


def make_kis_secrets() -> KisSecrets:
    """Build test KIS secrets."""
    return KisSecrets(
        app_key="test-app-key",
        app_secret="test-app-secret",
        account_no="12345678",
        account_type="mock",
    )
