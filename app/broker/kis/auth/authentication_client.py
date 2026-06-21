"""KIS OAuth, Approval, and HashKey authentication client."""

from __future__ import annotations

import logging
from typing import Any

from app.broker.kis.auth.auth_models import AccessToken, ApprovalKey, build_access_token
from app.broker.kis.auth.http_transport import HttpTransport, UrllibHttpTransport
from app.broker.kis.exceptions import (
    ApprovalKeyError,
    HashKeyError,
    InvalidCredentialError,
    TokenRefreshError,
)
from app.core.constants import (
    APP_NAME,
    APP_VERSION,
    KIS_HASHKEY_PATH,
    KIS_OAUTH_APPROVAL_PATH,
    KIS_OAUTH_TOKEN_PATH,
)

logger = logging.getLogger(__name__)

OAUTH_GRANT_TYPE = "client_credentials"
DEFAULT_USER_AGENT = f"{APP_NAME}/{APP_VERSION}"


class AuthenticationClient:
    """Low-level client for KIS authentication endpoints only."""

    def __init__(
        self,
        *,
        base_url: str,
        transport: HttpTransport | None = None,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        """Initialize the authentication client.

        Args:
            base_url: KIS REST base URL for the active environment.
            transport: Injectable HTTP transport for testing.
            user_agent: User-Agent header value.
        """
        self._base_url = base_url.rstrip("/")
        self._transport = transport or UrllibHttpTransport()
        self._user_agent = user_agent

    @property
    def base_url(self) -> str:
        """Return the configured REST base URL."""
        return self._base_url

    def build_base_headers(self) -> dict[str, str]:
        """Build base headers required by KIS OAuth endpoints.

        Returns:
            Header dictionary matching the official sample.
        """
        return {
            "Content-Type": "application/json",
            "Accept": "text/plain",
            "charset": "UTF-8",
            "User-Agent": self._user_agent,
        }

    def issue_access_token(self, app_key: str, app_secret: str) -> AccessToken:
        """Issue an OAuth access token via ``POST /oauth2/tokenP``.

        Args:
            app_key: KIS application key.
            app_secret: KIS application secret.

        Returns:
            Parsed access token model.

        Raises:
            InvalidCredentialError: When credentials are missing.
            TokenRefreshError: When the API returns a non-success response.
        """
        if not app_key or not app_secret:
            msg = "KIS app key and app secret are required for token issuance"
            raise InvalidCredentialError(msg)

        url = f"{self._base_url}{KIS_OAUTH_TOKEN_PATH}"
        body = {
            "grant_type": OAUTH_GRANT_TYPE,
            "appkey": app_key,
            "appsecret": app_secret,
        }
        response = self._transport.post_json(url, self.build_base_headers(), body)
        if response.status_code != 200:
            msg = f"Access token issuance failed with status {response.status_code}"
            logger.error(msg)
            raise TokenRefreshError(msg)

        token = response.body.get("access_token")
        expired_at = response.body.get("access_token_token_expired")
        if not isinstance(token, str) or not isinstance(expired_at, str):
            msg = "Access token response is missing required fields"
            logger.error(msg)
            raise TokenRefreshError(msg)

        access_token = build_access_token(token, expired_at)
        logger.info("KIS access token issued successfully")
        return access_token

    def issue_approval_key(
        self,
        app_key: str,
        app_secret: str,
        *,
        access_token: str | None = None,
    ) -> ApprovalKey:
        """Issue a WebSocket approval key via ``POST /oauth2/Approval``.

        Args:
            app_key: KIS application key.
            app_secret: KIS application secret.
            access_token: Optional REST access token included in the request body.

        Returns:
            Parsed approval key model.

        Raises:
            InvalidCredentialError: When credentials are missing.
            ApprovalKeyError: When the API returns a non-success response.
        """
        if not app_key or not app_secret:
            msg = "KIS app key and app secret are required for approval key issuance"
            raise InvalidCredentialError(msg)

        url = f"{self._base_url}{KIS_OAUTH_APPROVAL_PATH}"
        body: dict[str, Any] = {
            "grant_type": OAUTH_GRANT_TYPE,
            "appkey": app_key,
            "secretkey": app_secret,
        }
        if access_token:
            body["token"] = access_token

        response = self._transport.post_json(url, self.build_base_headers(), body)
        if response.status_code != 200:
            msg = f"Approval key issuance failed with status {response.status_code}"
            logger.error(msg)
            raise ApprovalKeyError(msg)

        approval_key = response.body.get("approval_key")
        if not isinstance(approval_key, str) or not approval_key:
            msg = "Approval key response is missing approval_key"
            logger.error(msg)
            raise ApprovalKeyError(msg)

        from datetime import UTC, datetime

        logger.info("KIS approval key issued successfully")
        return ApprovalKey(key=approval_key, issued_at=datetime.now(UTC))

    def issue_hash_key(
        self,
        headers: dict[str, str],
        body: dict[str, Any],
    ) -> str:
        """Issue an order hash key via ``POST /uapi/hashkey``.

        Args:
            headers: Authenticated REST headers including app key and secret.
            body: Order request body to hash.

        Returns:
            Hash key string.

        Raises:
            HashKeyError: When the API returns a non-success response.
        """
        url = f"{self._base_url}{KIS_HASHKEY_PATH}"
        request_headers = dict(headers)
        request_headers.setdefault("Content-Type", "application/json")
        request_headers.setdefault("Accept", "text/plain")
        request_headers.setdefault("charset", "UTF-8")
        request_headers.setdefault("User-Agent", self._user_agent)

        response = self._transport.post_json(url, request_headers, body)
        if response.status_code != 200:
            msg = f"HashKey issuance failed with status {response.status_code}"
            logger.error(msg)
            raise HashKeyError(msg)

        hash_value = response.body.get("HASH")
        if not isinstance(hash_value, str) or not hash_value:
            msg = "HashKey response is missing HASH field"
            logger.error(msg)
            raise HashKeyError(msg)

        logger.info("KIS hash key issued successfully")
        return hash_value
