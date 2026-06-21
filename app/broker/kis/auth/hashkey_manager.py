"""Order hash key manager for KIS OpenAPI."""

from __future__ import annotations

import logging
from typing import Any

from app.broker.kis.auth.authentication_client import AuthenticationClient
from app.broker.kis.auth.header_builder import HeaderBuilder
from app.broker.kis.auth.token_manager import TokenManager

logger = logging.getLogger(__name__)


class HashKeyManager:
    """Generates KIS order hash keys on demand."""

    def __init__(
        self,
        *,
        auth_client: AuthenticationClient,
        token_manager: TokenManager,
        header_builder: HeaderBuilder,
    ) -> None:
        """Initialize hash key manager dependencies.

        Args:
            auth_client: Low-level authentication HTTP client.
            token_manager: Access token manager for authenticated headers.
            header_builder: Header builder for REST requests.
        """
        self._auth_client = auth_client
        self._token_manager = token_manager
        self._header_builder = header_builder

    def generate(
        self,
        body: dict[str, Any],
        *,
        tr_id: str | None = None,
    ) -> str:
        """Generate a hash key for an order request body.

        Args:
            body: Order request payload to hash.
            tr_id: Optional transaction ID added to headers when provided.

        Returns:
            Generated hash key string.
        """
        access_token = self._token_manager.get_token()
        if tr_id:
            headers = self._header_builder.build_tr_headers(access_token, tr_id)
        else:
            headers = self._header_builder.build_auth_headers(access_token)

        hash_value = self._auth_client.issue_hash_key(headers, body)
        logger.info("Hash key generated for order request")
        return hash_value

    def generate_headers(
        self,
        body: dict[str, Any],
        tr_id: str,
    ) -> dict[str, str]:
        """Build authenticated headers including hash key for an order request.

        Args:
            body: Order request payload to hash.
            tr_id: KIS transaction ID.

        Returns:
            Header dictionary including ``hashkey``.
        """
        access_token = self._token_manager.get_token()
        hash_value = self.generate(body, tr_id=tr_id)
        headers = self._header_builder.build_tr_headers(
            access_token,
            tr_id,
            hashkey=hash_value,
        )
        return headers
