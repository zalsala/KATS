"""Unit tests for HashKeyManager."""

from __future__ import annotations

from pathlib import Path

import pytest
from tests.fixtures.auth_fixtures import MockHttpTransport, make_auth_config

from app.broker.kis.auth.authentication_client import AuthenticationClient
from app.broker.kis.auth.hashkey_manager import HashKeyManager
from app.broker.kis.auth.header_builder import HeaderBuilder
from app.broker.kis.auth.token_cache import TokenCache
from app.broker.kis.auth.token_manager import TokenManager

pytestmark = pytest.mark.unit


def _build_manager(tmp_path: Path) -> tuple[HashKeyManager, MockHttpTransport]:
    transport = MockHttpTransport()
    auth_config = make_auth_config()
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
    header_builder = HeaderBuilder(
        app_key=auth_config.app_key,
        app_secret=auth_config.app_secret,
    )
    manager = HashKeyManager(
        auth_client=client,
        token_manager=token_manager,
        header_builder=header_builder,
    )
    return manager, transport


class TestHashKeyManager:
    """Tests for HashKeyManager."""

    def test_generate_hash_key(self, tmp_path: Path) -> None:
        """generate() returns hash key from mock API."""
        manager, transport = _build_manager(tmp_path)

        hash_value = manager.generate({"PDNO": "005930", "ORD_QTY": "1"}, tr_id="TTTC0012U")

        assert hash_value == "mock-hash-key"
        assert any("/uapi/hashkey" in call[0] for call in transport.calls)

    def test_generate_headers_includes_hashkey(self, tmp_path: Path) -> None:
        """generate_headers() returns complete order headers."""
        manager, _ = _build_manager(tmp_path)

        headers = manager.generate_headers(
            {"PDNO": "005930", "ORD_QTY": "1"},
            tr_id="TTTC0012U",
        )

        assert headers["hashkey"] == "mock-hash-key"
        assert headers["tr_id"] == "TTTC0012U"
        assert headers["authorization"].startswith("Bearer ")
