"""Market repository interface."""

from __future__ import annotations

from typing import Protocol

from app.domain.market.entities.asking_price import AskingPrice
from app.domain.market.entities.stock_price import StockPrice
from app.domain.market.value_objects.symbol import Symbol


class IMarketRepository(Protocol):
    """Market data access interface."""

    def get_current_price(self, symbol: Symbol) -> StockPrice:
        """Return the current price for a symbol.

        Args:
            symbol: Stock symbol value object.

        Returns:
            Current price entity.
        """
        ...

    def get_asking_price(self, symbol: Symbol) -> AskingPrice:
        """Return bid/ask levels for a symbol.

        Args:
            symbol: Stock symbol value object.

        Returns:
            Asking price entity.
        """
        ...
