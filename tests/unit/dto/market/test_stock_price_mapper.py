"""DTO mapping tests for stock price."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from tests.fixtures.market_fixtures import sample_price_output

from app.domain.market.value_objects.symbol import Symbol
from app.dto.market.inquire_price_dto import InquirePriceResponseDto
from app.dto.market.mappers.stock_price_mapper import StockPriceMapper

pytestmark = pytest.mark.unit


class TestStockPriceMapper:
    """Tests for StockPriceMapper."""

    def test_to_entity_maps_kis_fields(self) -> None:
        """Mapper converts KIS output DTO to StockPrice entity."""
        dto = InquirePriceResponseDto.from_api_output(sample_price_output())
        queried_at = datetime(2026, 6, 20, tzinfo=UTC)
        symbol = Symbol("005930")

        entity = StockPriceMapper.to_entity(dto, symbol=symbol, queried_at=queried_at)

        assert entity.symbol.code == "005930"
        assert entity.stock_name == "삼성전자"
        assert entity.current_price == Decimal("70000")
        assert entity.change_amount == Decimal("500")
        assert entity.change_rate == Decimal("0.72")
        assert entity.queried_at == queried_at

    def test_from_api_output_parses_output_dict(self) -> None:
        """Response DTO parses official KIS field names."""
        dto = InquirePriceResponseDto.from_api_output(sample_price_output())

        assert dto.stock_code == "005930"
        assert dto.current_price == "70000"
