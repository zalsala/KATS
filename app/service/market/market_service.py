"""Market application service."""

from __future__ import annotations

from app.domain.market.entities.asking_price import AskingPrice
from app.domain.market.entities.stock_price import StockPrice
from app.repository.interfaces.market_repository import IMarketRepository
from app.service.market.usecases.get_asking_price_use_case import GetAskingPriceUseCase
from app.service.market.usecases.get_current_price_use_case import GetCurrentPriceUseCase


class MarketService:
    """Application service for market data use cases."""

    def __init__(
        self,
        *,
        market_repository: IMarketRepository,
        get_current_price_use_case: GetCurrentPriceUseCase | None = None,
        get_asking_price_use_case: GetAskingPriceUseCase | None = None,
    ) -> None:
        """Initialize market service dependencies.

        Args:
            market_repository: Market repository interface.
            get_current_price_use_case: Optional injected current price use case.
            get_asking_price_use_case: Optional injected asking price use case.
        """
        self._market_repository = market_repository
        self._get_current_price = get_current_price_use_case or GetCurrentPriceUseCase(
            market_repository
        )
        self._get_asking_price = get_asking_price_use_case or GetAskingPriceUseCase(
            market_repository
        )

    def get_current_price(self, symbol_code: str) -> StockPrice:
        """Return the current price for a stock symbol."""
        return self._get_current_price.execute(symbol_code)

    def get_asking_price(self, symbol_code: str) -> AskingPrice:
        """Return bid and ask levels for a stock symbol."""
        return self._get_asking_price.execute(symbol_code)


def build_market_service(
    *,
    market_repository: IMarketRepository,
) -> MarketService:
    """Create a ``MarketService`` wired with default use cases.

    Args:
        market_repository: Market repository implementation.

    Returns:
        Configured market service.
    """
    return MarketService(market_repository=market_repository)
