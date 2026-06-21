"""REST client interface for broker layer."""

from __future__ import annotations

from typing import Any, Protocol

from app.broker.kis.rest.api_result import ApiResult


class RestClient(Protocol):
    """Broker REST client interface."""

    def get(
        self,
        path: str,
        tr_id: str,
        params: dict[str, Any] | None = None,
        *,
        raise_on_error: bool = True,
    ) -> ApiResult:
        """Execute an authenticated GET request.

        Args:
            path: API path relative to the REST base URL.
            tr_id: KIS transaction ID.
            params: Optional query parameters.
            raise_on_error: Raise mapped exception when the call fails.

        Returns:
            Parsed API result.
        """
        ...

    def post(
        self,
        path: str,
        tr_id: str,
        body: dict[str, Any] | None = None,
        *,
        hashkey: str | None = None,
        raise_on_error: bool = True,
    ) -> ApiResult:
        """Execute an authenticated POST request.

        Args:
            path: API path relative to the REST base URL.
            tr_id: KIS transaction ID.
            body: Optional JSON request body.
            hashkey: Optional hash key for order requests.
            raise_on_error: Raise mapped exception when the call fails.

        Returns:
            Parsed API result.
        """
        ...
