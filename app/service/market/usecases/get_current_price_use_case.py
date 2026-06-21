"""Get current price use case."""

from __future__ import annotations

from app.domain.market.entities.stock_price import StockPrice
from app.domain.market.value_objects.symbol import Symbol
from app.repository.interfaces.market_repository import IMarketRepository


class GetCurrentPriceUseCase:
    """Retrieve the current price for a stock symbol."""

    def __init__(self, market_repository: IMarketRepository) -> None:
        """Initialize use case dependencies.

        Args:
            market_repository: Market repository interface.
        """
        self._market_repository = market_repository

    def execute(self, symbol_code: str) -> StockPrice:
        """Execute the current price inquiry use case.

        Args:
            symbol_code: Six-digit stock symbol.

        Returns:
            Current price domain entity.
        """
        symbol = Symbol(symbol_code)
        return self._market_repository.get_current_price(symbol)
