"""WebSocket approval key manager for KIS OpenAPI."""

from __future__ import annotations

import logging
import threading
from datetime import UTC, datetime, timedelta

from app.broker.kis.auth.auth_models import ApprovalKey
from app.broker.kis.auth.authentication_client import AuthenticationClient
from app.broker.kis.auth.token_cache import TokenCache
from app.broker.kis.auth.token_manager import TokenManager
from app.broker.kis.exceptions import InvalidCredentialError
from app.config.config_models import AuthenticationConfig

logger = logging.getLogger(__name__)


class ApprovalKeyManager:
    """Manages KIS WebSocket approval keys with cache support."""

    def __init__(
        self,
        *,
        auth_config: AuthenticationConfig,
        auth_client: AuthenticationClient,
        token_cache: TokenCache,
        token_manager: TokenManager,
    ) -> None:
        """Initialize approval key manager dependencies.

        Args:
            auth_config: Authentication configuration including cache duration.
            auth_client: Low-level authentication HTTP client.
            token_cache: Shared cache for approval key persistence.
            token_manager: Access token manager used before approval issuance.
        """
        self._auth_config = auth_config
        self._auth_client = auth_client
        self._token_cache = token_cache
        self._token_manager = token_manager
        self._lock = threading.RLock()
        self._memory_issued_at: datetime | None = None

    def get_approval_key(self, *, force_refresh: bool = False) -> ApprovalKey:
        """Return a valid approval key, refreshing when required.

        Args:
            force_refresh: When True, bypass cache and request a new key.

        Returns:
            Valid approval key instance.
        """
        with self._lock:
            if not force_refresh:
                cached = self._token_cache.get_approval_key()
                if cached is not None and not self._is_cache_expired(cached):
                    return cached
            return self.issue()

    def issue(self) -> ApprovalKey:
        """Issue a new approval key after ensuring a valid access token exists.

        Returns:
            Newly issued approval key.
        """
        self._validate_credentials()
        access_token = self._token_manager.get_token()
        approval = self._auth_client.issue_approval_key(
            self._auth_config.app_key,
            self._auth_config.app_secret,
            access_token=access_token.token,
        )
        self._token_cache.save_approval_key(approval)
        self._memory_issued_at = approval.issued_at
        logger.info("Approval key issued and cached")
        return approval

    def invalidate(self) -> None:
        """Clear cached approval key."""
        with self._lock:
            self._token_cache.clear_approval_key()
            self._memory_issued_at = None
            logger.info("Approval key cache invalidated")

    def _is_cache_expired(self, approval: ApprovalKey) -> bool:
        issued_at = self._memory_issued_at or approval.issued_at
        expiry = issued_at + timedelta(seconds=self._auth_config.approval_cache_seconds)
        return datetime.now(UTC) >= expiry

    def _validate_credentials(self) -> None:
        if not self._auth_config.app_key or not self._auth_config.app_secret:
            msg = "KIS credentials are not configured"
            raise InvalidCredentialError(msg)
