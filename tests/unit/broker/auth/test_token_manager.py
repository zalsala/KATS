"""Unit tests for TokenManager."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from tests.fixtures.auth_fixtures import MockHttpTransport, make_auth_config

from app.broker.kis.auth.auth_models import AccessToken
from app.broker.kis.auth.authentication_client import AuthenticationClient
from app.broker.kis.auth.token_cache import TokenCache
from app.broker.kis.auth.token_manager import TokenManager
from app.broker.kis.exceptions import InvalidCredentialError, TokenExpiredError

pytestmark = pytest.mark.unit


def _build_manager(
    tmp_path: Path,
    *,
    transport: MockHttpTransport | None = None,
    auto_refresh: bool = True,
    refresh_margin_seconds: int = 300,
) -> tuple[TokenManager, MockHttpTransport]:
    transport = transport or MockHttpTransport()
    auth_config = make_auth_config(
        auto_refresh=auto_refresh,
        refresh_margin_seconds=refresh_margin_seconds,
    )
    client = AuthenticationClient(
        base_url="https://openapivts.koreainvestment.com:29443",
        transport=transport,
    )
    cache = TokenCache(token_path=tmp_path / "token.json")
    manager = TokenManager(
        auth_config=auth_config,
        auth_client=client,
        token_cache=cache,
    )
    return manager, transport


class TestTokenManagerIssue:
    """Tests for token issuance."""

    def test_issue_requests_new_token(self, tmp_path: Path) -> None:
        """issue() calls OAuth and caches the token."""
        manager, transport = _build_manager(tmp_path)

        token = manager.issue()

        assert token.token == "mock-access-token"
        assert transport.token_call_count == 1
        assert manager._token_cache.get_access_token() is not None

    def test_issue_requires_credentials(self, tmp_path: Path) -> None:
        """issue() raises when credentials are missing."""
        transport = MockHttpTransport()
        auth_config = make_auth_config(app_key="", app_secret="")
        client = AuthenticationClient(
            base_url="https://openapivts.koreainvestment.com:29443",
            transport=transport,
        )
        manager = TokenManager(
            auth_config=auth_config,
            auth_client=client,
            token_cache=TokenCache(token_path=tmp_path / "token.json"),
        )

        with pytest.raises(InvalidCredentialError):
            manager.issue()


class TestTokenManagerExpire:
    """Tests for token expiry detection."""

    def test_is_expired_when_token_missing(self, tmp_path: Path) -> None:
        """Missing token is treated as expired."""
        manager, _ = _build_manager(tmp_path)

        assert manager.is_expired() is True

    def test_is_expired_when_past_expiry(self, tmp_path: Path) -> None:
        """Expired token returns True."""
        manager, _ = _build_manager(tmp_path)
        expired = TokenManager.create_expired_token()

        assert manager.is_expired(expired) is True

    def test_is_expired_within_refresh_margin(self, tmp_path: Path) -> None:
        """Token inside refresh margin is treated as expired."""
        manager, _ = _build_manager(tmp_path, refresh_margin_seconds=600)
        now = datetime.now(UTC)
        token = AccessToken(
            token="near-expiry",
            expires_at=now + timedelta(seconds=120),
            issued_at=now - timedelta(hours=1),
        )

        assert manager.is_expired(token) is True

    def test_is_not_expired_when_valid(self, tmp_path: Path) -> None:
        """Valid token with sufficient remaining time is not expired."""
        manager, _ = _build_manager(tmp_path)
        now = datetime.now(UTC)
        token = AccessToken(
            token="valid-token",
            expires_at=now + timedelta(hours=2),
            issued_at=now,
        )

        assert manager.is_expired(token) is False


class TestTokenManagerRefresh:
    """Tests for token refresh behavior."""

    def test_get_token_uses_cached_valid_token(self, tmp_path: Path) -> None:
        """get_token() returns cached token without API call."""
        manager, transport = _build_manager(tmp_path)
        manager.issue()

        token = manager.get_token()

        assert token.token == "mock-access-token"
        assert transport.token_call_count == 1

    def test_get_token_refreshes_expired_token(self, tmp_path: Path) -> None:
        """get_token() refreshes when cached token is expired."""
        manager, transport = _build_manager(tmp_path)
        cache = manager._token_cache
        cache.save_access_token(TokenManager.create_expired_token("old-token"))

        token = manager.get_token()

        assert token.token == "mock-access-token"
        assert transport.token_call_count == 1

    def test_refresh_skips_api_when_token_still_valid(self, tmp_path: Path) -> None:
        """refresh() reuses valid cached token."""
        manager, transport = _build_manager(tmp_path)
        manager.issue()

        token = manager.refresh()

        assert token.token == "mock-access-token"
        assert transport.token_call_count == 1

    def test_refresh_issues_new_token_when_expired(self, tmp_path: Path) -> None:
        """refresh() requests new token when cache is expired."""
        manager, transport = _build_manager(tmp_path)
        manager._token_cache.save_access_token(TokenManager.create_expired_token())

        token = manager.refresh()

        assert token.token == "mock-access-token"
        assert transport.token_call_count == 1

    def test_get_token_raises_when_auto_refresh_disabled(self, tmp_path: Path) -> None:
        """Expired token with auto_refresh=False raises TokenExpiredError."""
        manager, _ = _build_manager(tmp_path, auto_refresh=False)
        manager._token_cache.save_access_token(TokenManager.create_expired_token())

        with pytest.raises(TokenExpiredError):
            manager.get_token()

    def test_concurrent_refresh_issues_token_once(self, tmp_path: Path) -> None:
        """Concurrent refresh calls issue token only once."""
        transport = MockHttpTransport()
        manager, _ = _build_manager(tmp_path, transport=transport)
        manager._token_cache.save_access_token(TokenManager.create_expired_token())

        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(lambda _: manager.refresh(), range(5)))

        assert all(token.token == "mock-access-token" for token in results)
        assert transport.token_call_count == 1
