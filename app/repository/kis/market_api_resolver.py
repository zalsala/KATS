"""Market API resolver using ApiRegistry."""

from __future__ import annotations

from dataclasses import dataclass

from app.broker.kis.api import ApiRegistry
from app.broker.kis.api.enums import HttpMethod
from app.broker.kis.api.market_api_keys import MARKET_QUOTATION_API_KEYS
from app.broker.kis.api.metadata import ApiMetadata


class MarketApiResolverError(Exception):
    """Raised when market API metadata cannot be resolved."""


class MarketApiNotFoundError(MarketApiResolverError):
    """Raised when an API key is missing from the registry."""


class MarketApiNotEnabledError(MarketApiResolverError):
    """Raised when an API is registered but disabled for KATS."""


@dataclass(frozen=True, slots=True)
class ResolvedMarketApi:
    """Resolved REST metadata for a market API call.

    Attributes:
        api_key: Registry API key.
        path: REST path.
        tr_id: Effective TR ID for the active environment.
        method: HTTP method.
    """

    api_key: str
    path: str
    tr_id: str
    method: HttpMethod


class MarketApiResolver:
    """Resolves market API keys to REST metadata via ``ApiRegistry``."""

    def __init__(
        self,
        registry: ApiRegistry,
        *,
        use_mock_tr_id: bool = True,
    ) -> None:
        """Initialize resolver.

        Args:
            registry: Combined KIS API registry.
            use_mock_tr_id: Use mock TR IDs when True.
        """
        self._registry = registry
        self._use_mock_tr_id = use_mock_tr_id

    def resolve(self, api_key: str) -> ResolvedMarketApi:
        """Resolve an API key to REST metadata.

        Args:
            api_key: Registry API key.

        Returns:
            Resolved REST metadata including TR ID.

        Raises:
            MarketApiNotFoundError: When the API key is unknown.
            MarketApiNotEnabledError: When the API is disabled.
            MarketApiResolverError: When TR ID metadata is missing.
        """
        if api_key not in MARKET_QUOTATION_API_KEYS:
            msg = f"Unsupported market API key: {api_key}"
            raise MarketApiResolverError(msg)

        metadata = self._registry.endpoints.get_by_key(api_key)
        if metadata is None:
            msg = f"Market API key not found in registry: {api_key}"
            raise MarketApiNotFoundError(msg)
        if not metadata.enabled:
            msg = f"Market API is disabled: {api_key}"
            raise MarketApiNotEnabledError(msg)

        tr_id = _select_tr_id(metadata, use_mock=self._use_mock_tr_id)
        if not tr_id:
            msg = f"Market API has no TR ID: {api_key}"
            raise MarketApiResolverError(msg)

        return ResolvedMarketApi(
            api_key=api_key,
            path=metadata.path,
            tr_id=tr_id,
            method=metadata.method,
        )


def _select_tr_id(metadata: ApiMetadata, *, use_mock: bool) -> str:
    if use_mock and metadata.mock_tr_id:
        return metadata.mock_tr_id
    return metadata.tr_id
