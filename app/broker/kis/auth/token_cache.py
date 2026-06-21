"""Token and approval key cache for KIS authentication."""

from __future__ import annotations

import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from app.broker.kis.auth.auth_models import AccessToken, ApprovalKey

logger = logging.getLogger(__name__)


class TokenCache:
    """Memory-first cache with optional disk persistence for auth artifacts."""

    def __init__(
        self,
        *,
        token_path: Path,
        approval_path: Path | None = None,
    ) -> None:
        """Initialize token cache paths.

        Args:
            token_path: File path for persisted access tokens.
            approval_path: File path for persisted approval keys.
        """
        self._token_path = token_path
        self._approval_path = approval_path or token_path.parent / "approval.json"
        self._lock = threading.RLock()
        self._memory_token: AccessToken | None = None
        self._memory_approval: ApprovalKey | None = None

    @property
    def token_path(self) -> Path:
        """Return the access token persistence path."""
        return self._token_path

    @property
    def approval_path(self) -> Path:
        """Return the approval key persistence path."""
        return self._approval_path

    def get_access_token(self) -> AccessToken | None:
        """Return a cached access token from memory or disk.

        Returns:
            Cached access token or None when unavailable.
        """
        with self._lock:
            if self._memory_token is not None:
                return self._memory_token
            token = self._load_access_token_from_disk()
            if token is not None:
                self._memory_token = token
            return token

    def save_access_token(self, token: AccessToken) -> None:
        """Persist an access token to memory and disk.

        Args:
            token: Access token to cache.
        """
        with self._lock:
            self._memory_token = token
            self._write_json(
                self._token_path,
                {
                    "access_token": token.token,
                    "expires_at": token.expires_at.isoformat(),
                    "issued_at": token.issued_at.isoformat(),
                },
            )
            logger.info("Access token cached to %s", self._token_path)

    def clear_access_token(self) -> None:
        """Remove cached access token from memory and disk."""
        with self._lock:
            self._memory_token = None
            if self._token_path.exists():
                self._token_path.unlink()

    def get_approval_key(self) -> ApprovalKey | None:
        """Return a cached approval key from memory or disk.

        Returns:
            Cached approval key or None when unavailable.
        """
        with self._lock:
            if self._memory_approval is not None:
                return self._memory_approval
            approval = self._load_approval_from_disk()
            if approval is not None:
                self._memory_approval = approval
            return approval

    def save_approval_key(self, approval: ApprovalKey) -> None:
        """Persist an approval key to memory and disk.

        Args:
            approval: Approval key to cache.
        """
        with self._lock:
            self._memory_approval = approval
            self._write_json(
                self._approval_path,
                {
                    "approval_key": approval.key,
                    "issued_at": approval.issued_at.isoformat(),
                },
            )
            logger.info("Approval key cached to %s", self._approval_path)

    def clear_approval_key(self) -> None:
        """Remove cached approval key from memory and disk."""
        with self._lock:
            self._memory_approval = None
            if self._approval_path.exists():
                self._approval_path.unlink()

    def _load_access_token_from_disk(self) -> AccessToken | None:
        data = self._read_json(self._token_path)
        if not data:
            return None
        token = data.get("access_token")
        expires_at = data.get("expires_at")
        issued_at = data.get("issued_at")
        if not isinstance(token, str) or not token:
            return None
        if not isinstance(expires_at, str) or not isinstance(issued_at, str):
            return None
        try:
            return AccessToken(
                token=token,
                expires_at=datetime.fromisoformat(expires_at),
                issued_at=datetime.fromisoformat(issued_at),
            )
        except ValueError:
            logger.warning("Invalid access token cache at %s", self._token_path)
            return None

    def _load_approval_from_disk(self) -> ApprovalKey | None:
        data = self._read_json(self._approval_path)
        if not data:
            return None
        key = data.get("approval_key")
        issued_at = data.get("issued_at")
        if not isinstance(key, str) or not key:
            return None
        if not isinstance(issued_at, str):
            return None
        try:
            return ApprovalKey(key=key, issued_at=datetime.fromisoformat(issued_at))
        except ValueError:
            logger.warning("Invalid approval key cache at %s", self._approval_path)
            return None

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            logger.warning("Failed to read cache file %s", path)
            return {}
        if isinstance(loaded, dict):
            return loaded
        return {}

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
