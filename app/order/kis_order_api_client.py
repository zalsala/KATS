"""KIS order API client — ApiRegistry + HashKeyManager + KisRestClient."""

from __future__ import annotations

import logging
from typing import Any

from app.broker.interfaces.rest_client import RestClient
from app.broker.kis.api import ApiRegistry
from app.broker.kis.auth.hashkey_manager import HashKeyManager
from app.broker.kis.rest.api_result import ApiResult

logger = logging.getLogger(__name__)


class KisOrderApiClientError(Exception):
    """Raised when order API metadata cannot be resolved."""


class KisOrderApiClient:
    """Posts order requests via KisRestClient with registry-resolved TR IDs."""

    def __init__(
        self,
        *,
        rest_client: RestClient,
        registry: ApiRegistry,
        hashkey_manager: HashKeyManager,
        use_mock_tr_id: bool = True,
    ) -> None:
        """Initialize client dependencies."""
        self._rest_client = rest_client
        self._registry = registry
        self._hashkey_manager = hashkey_manager
        self._use_mock_tr_id = use_mock_tr_id

    def post(self, api_key: str, body: dict[str, Any]) -> ApiResult:
        """Execute a POST order API with HashKey when required."""
        path, tr_id, requires_hashkey = self._resolve(api_key)
        hashkey: str | None = None
        if requires_hashkey:
            hashkey = self._hashkey_manager.generate(body, tr_id=tr_id)
        logger.info("Order POST %s tr_id=%s hashkey=%s", api_key, tr_id, bool(hashkey))
        return self._rest_client.post(path, tr_id, body=body, hashkey=hashkey)

    def _resolve(self, api_key: str) -> tuple[str, str, bool]:
        metadata = self._registry.endpoints.get_by_key(api_key)
        if metadata is None:
            msg = f"API key not found in registry: {api_key}"
            raise KisOrderApiClientError(msg)
        if not metadata.enabled:
            msg = f"API is disabled: {api_key}"
            raise KisOrderApiClientError(msg)
        tr_id = metadata.tr_id
        if self._use_mock_tr_id and metadata.mock_tr_id:
            tr_id = metadata.mock_tr_id
        if not tr_id:
            msg = f"API has no TR ID: {api_key}"
            raise KisOrderApiClientError(msg)
        return metadata.path, tr_id, metadata.requires_hashkey
