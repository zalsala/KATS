"""Unit tests for KIS API enums and metadata."""

from __future__ import annotations

import pytest

from app.broker.kis.api.enums import ApiCategory, HttpMethod
from app.broker.kis.api.metadata import ApiMetadata, resolve_mock_tr_id

pytestmark = pytest.mark.unit


class TestEnums:
    """Tests for API enums."""

    def test_api_category_values_match_official_folders(self) -> None:
        """ApiCategory includes official GitHub example folders."""
        assert ApiCategory.AUTH.value == "auth"
        assert ApiCategory.DOMESTIC_STOCK.value == "domestic_stock"
        assert ApiCategory.OVERSEAS_STOCK.value == "overseas_stock"
        assert ApiCategory.ETFETN.value == "etfetn"

    def test_http_method_values(self) -> None:
        """HttpMethod supports GET and POST."""
        assert HttpMethod.GET.value == "GET"
        assert HttpMethod.POST.value == "POST"


class TestApiMetadata:
    """Tests for ApiMetadata."""

    def test_resolve_mock_tr_id(self) -> None:
        """Mock TR ID follows official V-prefix conversion."""
        assert resolve_mock_tr_id("TTTC0012U") == "VTTC0012U"
        assert resolve_mock_tr_id("FHKST01010100") == "FHKST01010100"

    def test_metadata_validation_success(self) -> None:
        """Valid metadata passes validation."""
        metadata = ApiMetadata(
            api_key="domestic_stock.inquire_price",
            name="Inquire Price",
            category=ApiCategory.DOMESTIC_STOCK,
            method=HttpMethod.GET,
            path="/uapi/domestic-stock/v1/quotations/inquire-price",
            tr_id="FHKST01010100",
            description="test",
        )

        metadata.validate()

    def test_metadata_validation_invalid_tr_id(self) -> None:
        """Invalid TR ID fails validation."""
        metadata = ApiMetadata(
            api_key="domestic_stock.invalid",
            name="Invalid",
            category=ApiCategory.DOMESTIC_STOCK,
            method=HttpMethod.GET,
            path="/uapi/domestic-stock/v1/quotations/inquire-price",
            tr_id="bad",
            description="test",
        )

        with pytest.raises(ValueError, match="tr_id"):
            metadata.validate()
