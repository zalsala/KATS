"""Unit tests for TR ID and endpoint registries."""

from __future__ import annotations

import pytest

from app.broker.kis.api.endpoint_registry import EndpointRegistry
from app.broker.kis.api.enums import ApiCategory, HttpMethod
from app.broker.kis.api.metadata import ApiMetadata
from app.broker.kis.api.tr_id_registry import TrIdRegistry

pytestmark = pytest.mark.unit


def _sample_metadata() -> ApiMetadata:
    return ApiMetadata(
        api_key="domestic_stock.inquire_price",
        name="Inquire Price",
        category=ApiCategory.DOMESTIC_STOCK,
        method=HttpMethod.GET,
        path="/uapi/domestic-stock/v1/quotations/inquire-price",
        tr_id="FHKST01010100",
        description="test",
    )


class TestTrIdRegistry:
    """Tests for TrIdRegistry."""

    def test_get_by_real_and_mock_tr_id(self) -> None:
        """Registry resolves both real and mock TR IDs."""
        registry = TrIdRegistry(entries=(_sample_metadata(),))

        real = registry.get("FHKST01010100")
        assert real is not None
        assert real.api_key == "domestic_stock.inquire_price"

    def test_duplicate_tr_id_registration_raises(self) -> None:
        """Duplicate TR ID mapping raises ValueError."""
        registry = TrIdRegistry(entries=())
        metadata = _sample_metadata()
        other = ApiMetadata(
            api_key="domestic_stock.other",
            name="Other",
            category=ApiCategory.DOMESTIC_STOCK,
            method=HttpMethod.GET,
            path="/uapi/domestic-stock/v1/quotations/inquire-asking-price",
            tr_id="FHKST01010200",
            description="other",
        )

        registry.register("TTTC0012U", metadata)
        with pytest.raises(ValueError, match="Duplicate tr_id"):
            registry.register("TTTC0012U", other)


class TestEndpointRegistry:
    """Tests for EndpointRegistry."""

    def test_get_by_method_and_path(self) -> None:
        """Endpoint lookup resolves method and path."""
        registry = EndpointRegistry(entries=(_sample_metadata(),))

        metadata = registry.get(HttpMethod.GET, "/uapi/domestic-stock/v1/quotations/inquire-price")

        assert metadata is not None
        assert metadata.tr_id == "FHKST01010100"

    def test_enabled_filters_disabled_entries(self) -> None:
        """Enabled filter excludes disabled category stubs."""
        registry = EndpointRegistry()

        enabled = registry.enabled()

        assert all(item.enabled for item in enabled)
        assert all(item.category != ApiCategory.DOMESTIC_BOND for item in enabled)

    def test_duplicate_endpoint_registration_raises(self) -> None:
        """Duplicate endpoint mapping raises ValueError."""
        registry = EndpointRegistry(entries=())
        metadata = _sample_metadata()
        duplicate = ApiMetadata(
            api_key="domestic_stock.duplicate",
            name="Duplicate",
            category=ApiCategory.DOMESTIC_STOCK,
            method=HttpMethod.GET,
            path="/uapi/domestic-stock/v1/quotations/inquire-price",
            tr_id="FHKST01010200",
            description="duplicate",
        )

        registry.register(metadata)
        with pytest.raises(ValueError, match="Duplicate endpoint"):
            registry.register(duplicate)
