"""Order API client interface."""

from __future__ import annotations

from typing import Any, Protocol

from app.broker.kis.rest.api_result import ApiResult


class OrderApiClient(Protocol):
    """Order API client backed by KisRestClient and ApiRegistry."""

    def post(self, api_key: str, body: dict[str, Any]) -> ApiResult:
        """Execute a registry-backed POST order API."""
        ...
