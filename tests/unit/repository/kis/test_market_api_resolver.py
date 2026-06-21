"""Tests for registry-backed market API resolution."""

from __future__ import annotations

import pytest

from app.broker.kis.api import ApiCategory, ApiMetadata, ApiRegistry, HttpMethod
from app.broker.kis.api.market_api_keys import INQUIRE_ASKING_PRICE, INQUIRE_PRICE
from app.repository.kis.market_api_resolver import (
    MarketApiNotEnabledError,
    MarketApiResolver,
    MarketApiResolverError,
)

pytestmark = pytest.mark.unit


class TestMarketApiResolver:
    """Tests for registry-backed market API resolution."""

    def test_resolve_inquire_price_from_default_registry(self) -> None:
        """Default registry resolves inquire price TR ID and path."""
        resolver = MarketApiResolver(ApiRegistry.default(), use_mock_tr_id=False)

        resolved = resolver.resolve(INQUIRE_PRICE)

        assert resolved.path == "/uapi/domestic-stock/v1/quotations/inquire-price"
        assert resolved.tr_id == "FHKST01010100"
        assert resolved.method == HttpMethod.GET

    def test_resolve_uses_registry_tr_id_for_asking_price(self) -> None:
        """Asking price API resolves its own TR ID from registry."""
        resolver = MarketApiResolver(ApiRegistry.default(), use_mock_tr_id=False)

        resolved = resolver.resolve(INQUIRE_ASKING_PRICE)

        assert resolved.tr_id == "FHKST01010200"

    def test_resolve_unknown_api_raises(self) -> None:
        """Unknown API keys raise MarketApiResolverError."""
        resolver = MarketApiResolver(ApiRegistry.default())

        with pytest.raises(MarketApiResolverError):
            resolver.resolve("domestic_stock.unknown")

    def test_resolve_disabled_api_raises(self) -> None:
        """Disabled registry entries raise MarketApiNotEnabledError."""
        disabled = ApiMetadata(
            api_key=INQUIRE_PRICE,
            name="Disabled",
            category=ApiCategory.DOMESTIC_STOCK,
            method=HttpMethod.GET,
            path="/uapi/domestic-stock/v1/quotations/inquire-price",
            tr_id="FHKST01010100",
            description="disabled",
            sub_category="quotations",
            enabled=False,
        )
        registry = ApiRegistry.from_entries((disabled,))
        resolver = MarketApiResolver(registry)

        with pytest.raises(MarketApiNotEnabledError):
            resolver.resolve(INQUIRE_PRICE)
