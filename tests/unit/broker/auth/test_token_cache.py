"""Unit tests for TokenCache."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from app.broker.kis.auth.auth_models import AccessToken, ApprovalKey
from app.broker.kis.auth.token_cache import TokenCache

pytestmark = pytest.mark.unit


def _access_token(token: str = "cached-token") -> AccessToken:
    now = datetime.now(UTC)
    return AccessToken(
        token=token,
        expires_at=now + timedelta(hours=1),
        issued_at=now,
    )


class TestTokenCache:
    """Tests for TokenCache persistence."""

    def test_save_and_load_access_token(self, tmp_path: Path) -> None:
        """Access token persists to disk and reloads into memory."""
        cache = TokenCache(token_path=tmp_path / "token.json")
        token = _access_token("persist-token")

        cache.save_access_token(token)
        loaded = cache.get_access_token()

        assert loaded is not None
        assert loaded.token == "persist-token"
        assert (tmp_path / "token.json").exists()

    def test_memory_cache_used_before_disk(self, tmp_path: Path) -> None:
        """Memory cache returns token without re-reading disk."""
        cache = TokenCache(token_path=tmp_path / "token.json")
        cache.save_access_token(_access_token("memory-token"))

        disk_text = (tmp_path / "token.json").read_text(encoding="utf-8")
        (tmp_path / "token.json").write_text(
            disk_text.replace("memory-token", "disk-token"),
            encoding="utf-8",
        )

        loaded = cache.get_access_token()
        assert loaded is not None
        assert loaded.token == "memory-token"

    def test_clear_access_token(self, tmp_path: Path) -> None:
        """clear_access_token removes memory and disk cache."""
        cache = TokenCache(token_path=tmp_path / "token.json")
        cache.save_access_token(_access_token())
        cache.clear_access_token()

        assert cache.get_access_token() is None
        assert not (tmp_path / "token.json").exists()

    def test_save_and_load_approval_key(self, tmp_path: Path) -> None:
        """Approval key persists to disk and reloads."""
        cache = TokenCache(token_path=tmp_path / "token.json")
        approval = ApprovalKey(key="approval-123", issued_at=datetime.now(UTC))

        cache.save_approval_key(approval)
        loaded = cache.get_approval_key()

        assert loaded is not None
        assert loaded.key == "approval-123"
