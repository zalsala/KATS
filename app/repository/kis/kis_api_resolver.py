"""Shared KIS API resolver for repository layers."""

from __future__ import annotations

from dataclasses import dataclass

from app.broker.kis.api import ApiRegistry
from app.broker.kis.api.enums import HttpMethod
from app.broker.kis.api.metadata import ApiMetadata


class KisApiResolverError(Exception):
    """Raised when API metadata cannot be resolved."""


class KisApiNotFoundError(KisApiResolverError):
    """Raised when an API key is missing from the registry."""


class KisApiNotEnabledError(KisApiResolverError):
    """Raised when an API is registered but disabled for KATS."""


@dataclass(frozen=True, slots=True)
class ResolvedKisApi:
    """Resolved REST metadata for a KIS API call."""

    api_key: str
    path: str
    tr_id: str
    method: HttpMethod
    requires_hashkey: bool = False


class KisApiResolver:
    """Resolves allowed API keys to REST metadata via ``ApiRegistry``."""

    def __init__(
        self,
        registry: ApiRegistry,
        allowed_api_keys: frozenset[str],
        *,
        use_mock_tr_id: bool = True,
    ) -> None:
        """Initialize resolver."""
        self._registry = registry
        self._allowed_api_keys = allowed_api_keys
        self._use_mock_tr_id = use_mock_tr_id

    def resolve(self, api_key: str) -> ResolvedKisApi:
        """Resolve an API key to REST metadata."""
        if api_key not in self._allowed_api_keys:
            msg = f"Unsupported API key: {api_key}"
            raise KisApiResolverError(msg)

        metadata = self._registry.endpoints.get_by_key(api_key)
        if metadata is None:
            msg = f"API key not found in registry: {api_key}"
            raise KisApiNotFoundError(msg)
        if not metadata.enabled:
            msg = f"API is disabled: {api_key}"
            raise KisApiNotEnabledError(msg)

        tr_id = _select_tr_id(metadata, use_mock=self._use_mock_tr_id)
        if not tr_id:
            msg = f"API has no TR ID: {api_key}"
            raise KisApiResolverError(msg)

        return ResolvedKisApi(
            api_key=api_key,
            path=metadata.path,
            tr_id=tr_id,
            method=metadata.method,
            requires_hashkey=metadata.requires_hashkey,
        )


def _select_tr_id(metadata: ApiMetadata, *, use_mock: bool) -> str:
    if use_mock and metadata.mock_tr_id:
        return metadata.mock_tr_id
    return metadata.tr_id
