"""Account API client backed by KisRestClient and ApiRegistry."""

from __future__ import annotations

import logging
from typing import Any

from app.broker.interfaces.rest_client import RestClient
from app.broker.kis.rest.api_result import ApiResult
from app.repository.kis.kis_api_resolver import KisApiResolver

logger = logging.getLogger(__name__)


class AccountApiClient:
    """Executes account APIs via ``KisRestClient`` with registry-resolved metadata."""

    def __init__(
        self,
        *,
        rest_client: RestClient,
        api_resolver: KisApiResolver,
    ) -> None:
        """Initialize account API client."""
        self._rest_client = rest_client
        self._api_resolver = api_resolver

    def get(self, api_key: str, params: dict[str, Any]) -> ApiResult:
        """Execute a registry-backed GET account API."""
        resolved = self._api_resolver.resolve(api_key)
        logger.info("Account API GET %s tr_id=%s", resolved.api_key, resolved.tr_id)
        return self._rest_client.get(
            resolved.path,
            resolved.tr_id,
            params=params,
        )
