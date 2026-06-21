"""Unit tests for ApprovalKeyManager."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from tests.fixtures.auth_fixtures import MockHttpTransport, make_auth_config

from app.broker.kis.auth.approval_key_manager import ApprovalKeyManager
from app.broker.kis.auth.auth_models import ApprovalKey
from app.broker.kis.auth.authentication_client import AuthenticationClient
from app.broker.kis.auth.token_cache import TokenCache
from app.broker.kis.auth.token_manager import TokenManager

pytestmark = pytest.mark.unit


def _build_manager(tmp_path: Path) -> tuple[ApprovalKeyManager, MockHttpTransport]:
    transport = MockHttpTransport()
    auth_config = make_auth_config(approval_cache_seconds=3600)
    client = AuthenticationClient(
        base_url="https://openapivts.koreainvestment.com:29443",
        transport=transport,
    )
    cache = TokenCache(token_path=tmp_path / "token.json")
    token_manager = TokenManager(
        auth_config=auth_config,
        auth_client=client,
        token_cache=cache,
    )
    manager = ApprovalKeyManager(
        auth_config=auth_config,
        auth_client=client,
        token_cache=cache,
        token_manager=token_manager,
    )
    return manager, transport


class TestApprovalKeyManager:
    """Tests for ApprovalKeyManager."""

    def test_issue_approval_key(self, tmp_path: Path) -> None:
        """issue() returns approval key from mock API."""
        manager, transport = _build_manager(tmp_path)

        approval = manager.issue()

        assert approval.key == "mock-approval-key"
        assert any("/oauth2/Approval" in call[0] for call in transport.calls)

    def test_get_approval_key_uses_cache(self, tmp_path: Path) -> None:
        """Second get_approval_key() uses cached value."""
        manager, transport = _build_manager(tmp_path)
        manager.issue()
        transport.calls.clear()

        approval = manager.get_approval_key()

        assert approval.key == "mock-approval-key"
        assert transport.calls == []

    def test_force_refresh_reissues_approval_key(self, tmp_path: Path) -> None:
        """force_refresh=True requests a new approval key."""
        manager, transport = _build_manager(tmp_path)
        manager.issue()
        transport.calls.clear()

        manager.get_approval_key(force_refresh=True)

        assert any("/oauth2/Approval" in call[0] for call in transport.calls)

    def test_cache_expired_reissues_approval_key(self, tmp_path: Path) -> None:
        """Expired approval cache triggers reissue."""
        auth_config = make_auth_config(approval_cache_seconds=60)
        transport = MockHttpTransport()
        client = AuthenticationClient(
            base_url="https://openapivts.koreainvestment.com:29443",
            transport=transport,
        )
        cache = TokenCache(token_path=tmp_path / "token.json")
        token_manager = TokenManager(
            auth_config=auth_config,
            auth_client=client,
            token_cache=cache,
        )
        manager = ApprovalKeyManager(
            auth_config=auth_config,
            auth_client=client,
            token_cache=cache,
            token_manager=token_manager,
        )
        stale = ApprovalKey(
            key="stale-key",
            issued_at=datetime.now(UTC) - timedelta(hours=2),
        )
        cache.save_approval_key(stale)
        transport.calls.clear()

        approval = manager.get_approval_key()

        assert approval.key == "mock-approval-key"
        assert any("/oauth2/Approval" in call[0] for call in transport.calls)
