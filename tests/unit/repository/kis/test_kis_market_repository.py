"""Mock KisRestClient tests for KisMarketRepository."""

from __future__ import annotations

from decimal import Decimal

import pytest
from tests.fixtures.market_fixtures import (
    MockRestClient,
    sample_asking_output,
    sample_price_output,
)

from app.broker.kis.api import ApiRegistry
from app.broker.kis.api.market_api_keys import INQUIRE_PRICE
from app.domain.market.value_objects.symbol import Symbol
from app.repository.kis.kis_market_repository import KisMarketRepository
from app.repository.kis.market_api_resolver import MarketApiResolver

pytestmark = pytest.mark.unit


class TestKisMarketRepository:
    """Tests for KisMarketRepository with mock REST client."""

    def test_get_current_price_uses_registry_tr_id_and_rest_client(self) -> None:
        """Repository resolves TR ID from registry and calls KisRestClient."""
        rest_client = MockRestClient(output=sample_price_output())
        repository = KisMarketRepository(
            rest_client=rest_client,
            api_resolver=MarketApiResolver(ApiRegistry.default(), use_mock_tr_id=False),
        )

        price = repository.get_current_price(Symbol("005930"))

        assert price.current_price == Decimal("70000")
        assert len(rest_client.calls) == 1
        call = rest_client.calls[0]
        assert call["tr_id"] == "FHKST01010100"
        assert call["path"] == "/uapi/domestic-stock/v1/quotations/inquire-price"
        assert call["params"]["FID_INPUT_ISCD"] == "005930"

    def test_get_asking_price_uses_asking_price_registry_entry(self) -> None:
        """Asking price uses separate registry metadata."""
        rest_client = MockRestClient(
            output_by_path={
                "/uapi/domestic-stock/v1/quotations/inquire-asking-price": sample_asking_output(),
            }
        )
        repository = KisMarketRepository(
            rest_client=rest_client,
            api_resolver=MarketApiResolver(ApiRegistry.default(), use_mock_tr_id=False),
        )

        asking = repository.get_asking_price(Symbol("005930"))

        assert len(asking.ask_levels) >= 1
        call = rest_client.calls[0]
        assert call["tr_id"] == "FHKST01010200"
        assert call["path"] == "/uapi/domestic-stock/v1/quotations/inquire-asking-price"

    def test_repository_does_not_hardcode_tr_id(self) -> None:
        """Changing registry metadata changes the TR ID used by repository."""
        from app.broker.kis.api.enums import ApiCategory, HttpMethod
        from app.broker.kis.api.metadata import ApiMetadata

        custom = ApiMetadata(
            api_key=INQUIRE_PRICE,
            name="Custom Price",
            category=ApiCategory.DOMESTIC_STOCK,
            method=HttpMethod.GET,
            path="/uapi/domestic-stock/v1/quotations/inquire-price",
            tr_id="CUSTOM000001",
            description="custom",
            sub_category="quotations",
            enabled=True,
        )
        registry = ApiRegistry.from_entries((custom,))
        rest_client = MockRestClient(output=sample_price_output())
        repository = KisMarketRepository(
            rest_client=rest_client,
            api_resolver=MarketApiResolver(registry, use_mock_tr_id=False),
        )

        repository.get_current_price(Symbol("005930"))

        assert rest_client.calls[0]["tr_id"] == "CUSTOM000001"
