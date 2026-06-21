"""Registry validation tests for the default KIS API framework."""

from __future__ import annotations

import pytest

from app.broker.kis.api import ApiCategory, ApiRegistry, HttpMethod
from app.broker.kis.api.endpoint_registry import EndpointRegistry
from app.broker.kis.api.metadata import ApiMetadata
from app.broker.kis.api.seeds.default_registry import DEFAULT_API_METADATA
from app.broker.kis.api.tr_id_registry import TrIdRegistry

pytestmark = pytest.mark.unit


class TestRegistryValidation:
    """Validation tests for the combined API registry."""

    def test_default_registry_validates(self) -> None:
        """Default seed registry passes full validation."""
        registry = ApiRegistry.default()

        registry.validate()

    def test_default_registry_contains_auth_and_domestic_stock(self) -> None:
        """Default registry includes auth and domestic stock metadata."""
        registry = ApiRegistry.default()

        auth_token = registry.endpoints.get_by_key("auth.oauth_token")
        inquire_price = registry.endpoints.get_by_key("domestic_stock.inquire_price")

        assert auth_token is not None
        assert inquire_price is not None
        assert inquire_price.category == ApiCategory.DOMESTIC_STOCK

    def test_tr_id_lookup_matches_endpoint_metadata(self) -> None:
        """TR ID registry and endpoint registry stay synchronized."""
        registry = ApiRegistry.default()
        metadata = registry.endpoints.get(
            HttpMethod.GET,
            "/uapi/domestic-stock/v1/quotations/inquire-price",
        )
        assert metadata is not None

        tr_lookup = registry.tr_ids.get("FHKST01010100")
        mock_lookup = registry.tr_ids.get("FHKST01010100")

        assert tr_lookup is not None
        assert tr_lookup.api_key == metadata.api_key
        assert mock_lookup is not None

    def test_mock_tr_id_registered_for_trading_api(self) -> None:
        """Trading APIs register mock TR IDs with V-prefix."""
        registry = ApiRegistry.default()

        real = registry.tr_ids.get("TTTC0012U")
        mock = registry.tr_ids.get("VTTC0012U")

        assert real is not None
        assert mock is not None
        assert real.api_key == mock.api_key == "domestic_stock.order_cash"

    def test_all_default_metadata_entries_are_valid(self) -> None:
        """Every seed metadata entry passes individual validation."""
        for metadata in DEFAULT_API_METADATA:
            metadata.validate()

    def test_custom_registry_detects_missing_tr_id(self) -> None:
        """Combined validation detects when endpoint TR ID is not registered."""
        endpoint_metadata = ApiMetadata(
            api_key="domestic_stock.broken",
            name="Broken",
            category=ApiCategory.DOMESTIC_STOCK,
            method=HttpMethod.GET,
            path="/uapi/domestic-stock/v1/quotations/inquire-asking-price",
            tr_id="FHKST01010200",
            description="broken",
        )
        tr_metadata = ApiMetadata(
            api_key="domestic_stock.inquire_price",
            name="Inquire Price",
            category=ApiCategory.DOMESTIC_STOCK,
            method=HttpMethod.GET,
            path="/uapi/domestic-stock/v1/quotations/inquire-price",
            tr_id="FHKST01010100",
            description="price",
        )
        registry = ApiRegistry(
            tr_ids=TrIdRegistry(entries=(tr_metadata,)),
            endpoints=EndpointRegistry(entries=(endpoint_metadata,)),
        )

        with pytest.raises(ValueError, match="missing from TR ID registry"):
            registry.validate()

    def test_disabled_categories_remain_registered(self) -> None:
        """Disabled categories remain in registry for future extension."""
        registry = ApiRegistry.default()

        bond = registry.endpoints.get_by_key("domestic_bond.stub")

        assert bond is not None
        assert bond.enabled is False

    def test_seed_count_is_stable(self) -> None:
        """Default seed set includes auth, enabled, and stub entries."""
        assert len(DEFAULT_API_METADATA) >= 14
