"""KIS REST request header builder."""

from __future__ import annotations

from typing import Any

from app.broker.kis.auth.auth_models import AccessToken
from app.core.constants import APP_NAME, APP_VERSION


class HeaderBuilder:
    """Builds KIS REST and WebSocket authentication headers."""

    def __init__(
        self,
        *,
        app_key: str,
        app_secret: str,
        user_agent: str = f"{APP_NAME}/{APP_VERSION}",
    ) -> None:
        """Initialize header builder with KIS credentials.

        Args:
            app_key: KIS application key.
            app_secret: KIS application secret.
            user_agent: User-Agent header value.
        """
        self._app_key = app_key
        self._app_secret = app_secret
        self._user_agent = user_agent

    def build_base_headers(self) -> dict[str, str]:
        """Build base headers used by OAuth endpoints.

        Returns:
            Base header dictionary.
        """
        return {
            "Content-Type": "application/json",
            "Accept": "text/plain",
            "charset": "UTF-8",
            "User-Agent": self._user_agent,
        }

    def build_auth_headers(self, access_token: AccessToken | str) -> dict[str, str]:
        """Build authenticated REST headers.

        Args:
            access_token: Access token model or raw token string.

        Returns:
            Header dictionary with authorization and app credentials.
        """
        token_value = access_token.token if isinstance(access_token, AccessToken) else access_token
        headers = self.build_base_headers()
        headers["authorization"] = f"Bearer {token_value}"
        headers["appkey"] = self._app_key
        headers["appsecret"] = self._app_secret
        return headers

    def build_tr_headers(
        self,
        access_token: AccessToken | str,
        tr_id: str,
        *,
        custtype: str = "P",
        hashkey: str | None = None,
        extra: dict[str, str] | None = None,
    ) -> dict[str, str]:
        """Build transaction REST headers for KIS API calls.

        Args:
            access_token: Access token model or raw token string.
            tr_id: KIS transaction ID.
            custtype: Customer type header value.
            hashkey: Optional hash key for order requests.
            extra: Optional additional headers.

        Returns:
            Complete REST header dictionary.
        """
        headers = self.build_auth_headers(access_token)
        headers["tr_id"] = tr_id
        headers["custtype"] = custtype
        if hashkey:
            headers["hashkey"] = hashkey
        if extra:
            headers.update(extra)
        return headers

    def build_ws_headers(self, approval_key: str) -> dict[str, str]:
        """Build WebSocket headers containing the approval key.

        Args:
            approval_key: WebSocket approval key.

        Returns:
            WebSocket header dictionary.
        """
        return {
            "approval_key": approval_key,
            "custtype": "P",
            "content-type": "utf-8",
        }

    def with_hashkey(
        self,
        headers: dict[str, str],
        body: dict[str, Any],
        hashkey: str,
    ) -> dict[str, str]:
        """Return a copy of headers with the hash key applied.

        Args:
            headers: Existing authenticated headers.
            body: Request body used for hash key generation.
            hashkey: Generated hash key value.

        Returns:
            Header dictionary including ``hashkey``.
        """
        _ = body
        updated = dict(headers)
        updated["hashkey"] = hashkey
        return updated
