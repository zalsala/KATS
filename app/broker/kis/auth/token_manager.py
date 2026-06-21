"""Access token lifecycle manager for KIS OpenAPI."""

from __future__ import annotations

import logging
import threading
from datetime import UTC, datetime

from app.broker.kis.auth.auth_models import AccessToken
from app.broker.kis.auth.authentication_client import AuthenticationClient
from app.broker.kis.auth.token_cache import TokenCache
from app.broker.kis.exceptions import InvalidCredentialError, TokenExpiredError
from app.config.config_models import AuthenticationConfig

logger = logging.getLogger(__name__)


class TokenManager:
    """Thread-safe manager for KIS OAuth access tokens."""

    def __init__(
        self,
        *,
        auth_config: AuthenticationConfig,
        auth_client: AuthenticationClient,
        token_cache: TokenCache,
    ) -> None:
        """Initialize token manager dependencies.

        Args:
            auth_config: Authentication configuration including refresh policy.
            auth_client: Low-level authentication HTTP client.
            token_cache: Token cache for memory and disk storage.
        """
        self._auth_config = auth_config
        self._auth_client = auth_client
        self._token_cache = token_cache
        self._lock = threading.RLock()
        self._refresh_lock = threading.Lock()

    def get_token(self, *, force_refresh: bool = False) -> AccessToken:
        """Return a valid access token, refreshing when required.

        Args:
            force_refresh: When True, bypass cache and request a new token.

        Returns:
            Valid access token instance.

        Raises:
            InvalidCredentialError: When credentials are missing.
            TokenExpiredError: When auto refresh is disabled and token expired.
        """
        with self._lock:
            if force_refresh:
                with self._refresh_lock:
                    return self.issue()

            cached = self._token_cache.get_access_token()
            if cached is not None and not self.is_expired(cached):
                return cached

            if self._auth_config.auto_refresh:
                return self.refresh()

            cached = self._token_cache.get_access_token()
            if cached is None:
                return self.issue()

            if self.is_expired(cached):
                msg = "Access token expired and auto refresh is disabled"
                raise TokenExpiredError(msg)
            return cached

    def issue(self) -> AccessToken:
        """Issue a new access token and persist it to cache.

        Returns:
            Newly issued access token.

        Raises:
            InvalidCredentialError: When credentials are missing.
        """
        self._validate_credentials()
        token = self._auth_client.issue_access_token(
            self._auth_config.app_key,
            self._auth_config.app_secret,
        )
        self._token_cache.save_access_token(token)
        logger.info("Access token issued and cached")
        return token

    def refresh(self) -> AccessToken:
        """Refresh the access token with duplicate-call protection.

        Returns:
            Refreshed access token.

        Raises:
            InvalidCredentialError: When credentials are missing.
        """
        with self._refresh_lock:
            cached = self._token_cache.get_access_token()
            if cached is not None and not self.is_expired(cached):
                return cached
            logger.info("Refreshing KIS access token")
            return self.issue()

    def is_expired(
        self,
        token: AccessToken | None = None,
        *,
        now: datetime | None = None,
    ) -> bool:
        """Check whether an access token is expired or near expiry.

        Args:
            token: Token to inspect. Uses cached token when omitted.
            now: Optional reference time in UTC.

        Returns:
            True when the token should be refreshed.
        """
        target = token or self._token_cache.get_access_token()
        if target is None:
            return True
        return target.is_expired(
            now=now,
            margin_seconds=self._auth_config.refresh_margin_seconds,
        )

    def invalidate(self) -> None:
        """Clear cached access token from memory and disk."""
        with self._lock:
            self._token_cache.clear_access_token()
            logger.info("Access token cache invalidated")

    def _validate_credentials(self) -> None:
        if not self._auth_config.app_key or not self._auth_config.app_secret:
            msg = "KIS credentials are not configured"
            raise InvalidCredentialError(msg)

    @staticmethod
    def create_expired_token(token_value: str = "expired-token") -> AccessToken:
        """Create an expired token helper for tests.

        Args:
            token_value: Token string value.

        Returns:
            Access token expired one hour ago.
        """
        from datetime import timedelta

        now = datetime.now(UTC)
        return AccessToken(
            token=token_value,
            expires_at=now - timedelta(hours=1),
            issued_at=now - timedelta(hours=2),
        )
