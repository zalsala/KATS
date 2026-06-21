"""Unit tests for market use cases and service."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.domain.market.entities.asking_price import AskingPrice, PriceLevel
from app.domain.market.entities.stock_price import StockPrice
from app.domain.market.value_objects.symbol import Symbol
from app.repository.interfaces.market_repository import IMarketRepository
from app.service.market.market_service import MarketService
from app.service.market.usecases.get_asking_price_use_case import GetAskingPriceUseCase
from app.service.market.usecases.get_current_price_use_case import GetCurrentPriceUseCase

pytestmark = pytest.mark.unit


class FakeMarketRepository:
    """In-memory market repository for use case tests."""

    def get_current_price(self, symbol: Symbol) -> StockPrice:
        return StockPrice(
            symbol=symbol,
            stock_name="테스트",
            current_price=Decimal("1000"),
            change_amount=Decimal("10"),
            change_rate=Decimal("1.0"),
            queried_at=datetime.now(UTC),
        )

    def get_asking_price(self, symbol: Symbol) -> AskingPrice:
        level = PriceLevel(price=Decimal("999"), quantity=Decimal("1"), level=1)
        return AskingPrice(
            symbol=symbol,
            stock_name="테스트",
            bid_levels=(level,),
            ask_levels=(level,),
            queried_at=datetime.now(UTC),
        )


class TestMarketUseCases:
    """Tests for market use cases."""

    def test_get_current_price_use_case(self) -> None:
        """Use case returns repository entity."""
        repository = FakeMarketRepository()
        use_case = GetCurrentPriceUseCase(repository)

        result = use_case.execute("005930")

        assert result.symbol.code == "005930"
        assert result.current_price == Decimal("1000")

    def test_get_asking_price_use_case(self) -> None:
        """Asking price use case returns repository entity."""
        repository = FakeMarketRepository()
        use_case = GetAskingPriceUseCase(repository)

        result = use_case.execute("005930")

        assert result.symbol.code == "005930"
        assert len(result.bid_levels) == 1


class TestMarketService:
    """Tests for MarketService."""

    def test_market_service_delegates_to_use_cases(self) -> None:
        """MarketService orchestrates use cases without REST access."""
        repository: IMarketRepository = FakeMarketRepository()
        service = MarketService(market_repository=repository)

        price = service.get_current_price("005930")
        asking = service.get_asking_price("005930")

        assert price.stock_name == "테스트"
        assert asking.stock_name == "테스트"
