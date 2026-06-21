"""REST request builder for KIS OpenAPI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from app.broker.kis.auth.header_builder import HeaderBuilder
from app.broker.kis.auth.token_manager import TokenManager
from app.broker.kis.rest.http_transport import build_url


@dataclass(frozen=True, slots=True)
class RestRequest:
    """Built REST request ready for transport execution.

    Attributes:
        url: Fully qualified request URL.
        method: HTTP method.
        headers: Request headers including authentication.
        body: JSON body for POST requests.
        tr_id: KIS transaction ID.
        path: API path relative to the REST base URL.
    """

    url: str
    method: Literal["GET", "POST"]
    headers: dict[str, str]
    body: dict[str, Any] | None
    tr_id: str
    path: str


class RequestBuilder:
    """Builds authenticated KIS REST requests."""

    def __init__(
        self,
        *,
        base_url: str,
        token_manager: TokenManager,
        header_builder: HeaderBuilder,
    ) -> None:
        """Initialize request builder dependencies.

        Args:
            base_url: KIS REST base URL.
            token_manager: Access token manager.
            header_builder: Header builder for authenticated requests.
        """
        self._base_url = base_url
        self._token_manager = token_manager
        self._header_builder = header_builder

    def build_get(
        self,
        path: str,
        tr_id: str,
        params: dict[str, Any] | None = None,
    ) -> RestRequest:
        """Build an authenticated GET request.

        Args:
            path: API path such as ``/uapi/domestic-stock/v1/quotations/inquire-price``.
            tr_id: KIS transaction ID.
            params: Optional query parameters.

        Returns:
            Built REST request.
        """
        access_token = self._token_manager.get_token()
        headers = self._header_builder.build_tr_headers(access_token, tr_id)
        return RestRequest(
            url=build_url(self._base_url, path, params),
            method="GET",
            headers=headers,
            body=None,
            tr_id=tr_id,
            path=path,
        )

    def build_post(
        self,
        path: str,
        tr_id: str,
        body: dict[str, Any] | None = None,
        *,
        hashkey: str | None = None,
    ) -> RestRequest:
        """Build an authenticated POST request.

        Args:
            path: API path.
            tr_id: KIS transaction ID.
            body: JSON request body.
            hashkey: Optional hash key for order requests.

        Returns:
            Built REST request.
        """
        access_token = self._token_manager.get_token()
        headers = self._header_builder.build_tr_headers(
            access_token,
            tr_id,
            hashkey=hashkey,
        )
        return RestRequest(
            url=build_url(self._base_url, path),
            method="POST",
            headers=headers,
            body=body or {},
            tr_id=tr_id,
            path=path,
        )
