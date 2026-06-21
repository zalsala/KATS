"""Mock integration tests for KIS authentication flow."""

from __future__ import annotations

from pathlib import Path

import pytest
from tests.fixtures.auth_fixtures import (
    MockHttpTransport,
    make_kats_config,
    make_kis_secrets,
)

from app.broker.kis.auth import build_authentication_components
from app.broker.kis.auth.token_manager import TokenManager
from app.config.app_settings import AppSettings

pytestmark = pytest.mark.unit


class TestMockAuthenticationFlow:
    """End-to-end mock authentication tests without real API calls."""

    def test_full_auth_flow(self, tmp_path: Path) -> None:
        """Token, approval, hashkey, and headers work together."""
        transport = MockHttpTransport()
        settings = AppSettings.create(
            project_root=tmp_path,
            config=make_kats_config(),
            secrets=make_kis_secrets(),
        )
        components = build_authentication_components(
            settings,
            token_path=tmp_path / "auth" / "token.json",
            transport=transport,
        )

        token = components.token_manager.get_token()
        approval = components.approval_key_manager.get_approval_key()
        headers = components.hashkey_manager.generate_headers(
            {"PDNO": "005930", "ORD_QTY": "1"},
            tr_id="TTTC0012U",
        )

        assert token.token == "mock-access-token"
        assert approval.key == "mock-approval-key"
        assert headers["hashkey"] == "mock-hash-key"
        assert headers["tr_id"] == "TTTC0012U"
        assert headers["authorization"].startswith("Bearer ")
        assert transport.token_call_count == 1

    def test_cached_token_skips_reissue(self, tmp_path: Path) -> None:
        """Second get_token() uses cache without additional OAuth calls."""
        transport = MockHttpTransport()
        settings = AppSettings.create(
            project_root=tmp_path,
            config=make_kats_config(),
            secrets=make_kis_secrets(),
        )
        components = build_authentication_components(
            settings,
            token_path=tmp_path / "auth" / "token.json",
            transport=transport,
        )

        components.token_manager.get_token()
        components.token_manager.get_token()

        assert transport.token_call_count == 1

    def test_token_expire_triggers_refresh_on_next_get(self, tmp_path: Path) -> None:
        """Expired cached token triggers refresh on next get_token()."""
        transport = MockHttpTransport()
        settings = AppSettings.create(
            project_root=tmp_path,
            config=make_kats_config(),
            secrets=make_kis_secrets(),
        )
        components = build_authentication_components(
            settings,
            token_path=tmp_path / "auth" / "token.json",
            transport=transport,
        )
        components.token_cache.save_access_token(TokenManager.create_expired_token("old"))

        token = components.token_manager.get_token()

        assert token.token == "mock-access-token"
        assert transport.token_call_count == 1

    def test_force_refresh_bypasses_valid_cache(self, tmp_path: Path) -> None:
        """force_refresh=True always requests a new token."""
        transport = MockHttpTransport()
        settings = AppSettings.create(
            project_root=tmp_path,
            config=make_kats_config(),
            secrets=make_kis_secrets(),
        )
        components = build_authentication_components(
            settings,
            token_path=tmp_path / "auth" / "token.json",
            transport=transport,
        )
        components.token_manager.get_token()

        components.token_manager.get_token(force_refresh=True)

        assert transport.token_call_count == 2

    def test_persisted_token_reloaded_after_restart(self, tmp_path: Path) -> None:
        """Token persisted to disk is reused by a new component bundle."""
        transport = MockHttpTransport()
        settings = AppSettings.create(
            project_root=tmp_path,
            config=make_kats_config(),
            secrets=make_kis_secrets(),
        )
        token_path = tmp_path / "auth" / "token.json"
        first = build_authentication_components(
            settings,
            token_path=token_path,
            transport=transport,
        )
        first.token_manager.issue()

        second_transport = MockHttpTransport()
        second = build_authentication_components(
            settings,
            token_path=token_path,
            transport=second_transport,
        )
        token = second.token_manager.get_token()

        assert token.token == "mock-access-token"
        assert second_transport.token_call_count == 0

    def test_approval_uses_access_token_in_request(self, tmp_path: Path) -> None:
        """Approval request includes REST access token when available."""
        transport = MockHttpTransport()
        settings = AppSettings.create(
            project_root=tmp_path,
            config=make_kats_config(),
            secrets=make_kis_secrets(),
        )
        components = build_authentication_components(
            settings,
            token_path=tmp_path / "auth" / "token.json",
            transport=transport,
        )
        components.token_manager.issue()
        transport.calls.clear()

        components.approval_key_manager.issue()

        approval_calls = [call for call in transport.calls if "/oauth2/Approval" in call[0]]
        assert len(approval_calls) == 1
        assert approval_calls[0][2]["token"] == "mock-access-token"
