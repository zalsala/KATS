"""Unit tests for HeaderBuilder."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.broker.kis.auth.auth_models import AccessToken
from app.broker.kis.auth.header_builder import HeaderBuilder

pytestmark = pytest.mark.unit


class TestHeaderBuilder:
    """Tests for HeaderBuilder."""

    def test_build_base_headers(self) -> None:
        """Base headers match official KIS OAuth requirements."""
        builder = HeaderBuilder(app_key="key", app_secret="secret")
        headers = builder.build_base_headers()

        assert headers["Content-Type"] == "application/json"
        assert headers["Accept"] == "text/plain"
        assert headers["charset"] == "UTF-8"
        assert "User-Agent" in headers

    def test_build_auth_headers(self) -> None:
        """Auth headers include bearer token and app credentials."""
        builder = HeaderBuilder(app_key="key", app_secret="secret")
        now = datetime.now(UTC)
        token = AccessToken(
            token="abc-token",
            expires_at=now + timedelta(hours=1),
            issued_at=now,
        )

        headers = builder.build_auth_headers(token)

        assert headers["authorization"] == "Bearer abc-token"
        assert headers["appkey"] == "key"
        assert headers["appsecret"] == "secret"

    def test_build_tr_headers_with_hashkey(self) -> None:
        """Transaction headers include tr_id, custtype, and hashkey."""
        builder = HeaderBuilder(app_key="key", app_secret="secret")
        headers = builder.build_tr_headers("token-value", "TTTC0012U", hashkey="hash-1")

        assert headers["tr_id"] == "TTTC0012U"
        assert headers["custtype"] == "P"
        assert headers["hashkey"] == "hash-1"

    def test_build_ws_headers(self) -> None:
        """WebSocket headers include approval key."""
        builder = HeaderBuilder(app_key="key", app_secret="secret")
        headers = builder.build_ws_headers("ws-approval")

        assert headers["approval_key"] == "ws-approval"
        assert headers["custtype"] == "P"
