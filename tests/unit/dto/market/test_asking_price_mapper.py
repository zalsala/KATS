"""DTO mapping tests for asking price."""

from __future__ import annotations

from decimal import Decimal

import pytest
from tests.fixtures.market_fixtures import sample_asking_output

from app.domain.market.value_objects.symbol import Symbol
from app.dto.market.inquire_asking_price_dto import InquireAskingPriceResponseDto
from app.dto.market.mappers.asking_price_mapper import AskingPriceMapper

pytestmark = pytest.mark.unit


class TestAskingPriceMapper:
    """Tests for AskingPriceMapper."""

    def test_to_entity_maps_price_levels(self) -> None:
        """Mapper converts bid/ask DTO fields into price levels."""
        dto = InquireAskingPriceResponseDto.from_api_output(sample_asking_output())
        symbol = Symbol("005930")

        entity = AskingPriceMapper.to_entity(dto, symbol=symbol)

        assert entity.symbol.code == "005930"
        assert len(entity.bid_levels) == 2
        assert entity.bid_levels[0].price == Decimal("69900")
        assert entity.ask_levels[0].price == Decimal("70000")
        assert entity.bid_levels[0].quantity == Decimal("100")
