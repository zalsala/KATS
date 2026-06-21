"""Strategy execution context."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from app.domain.portfolio.portfolio_snapshot import PortfolioSnapshot


@dataclass(slots=True)
class StrategyContext:
    """Read-only runtime context passed to strategies."""

    strategy_id: str
    strategy_name: str
    symbols: tuple[str, ...]
    parameters: dict[str, Any]
    portfolio_snapshot: PortfolioSnapshot | None = None
    price_cache: dict[str, Decimal] = field(default_factory=dict)
    custom_state: dict[str, Any] = field(default_factory=dict)
    logger: logging.Logger | None = None

    def get_position_quantity(self, symbol_code: str) -> Decimal:
        """Return held quantity for a symbol."""
        if self.portfolio_snapshot is None:
            return Decimal("0")
        for position in self.portfolio_snapshot.positions:
            if position.symbol_code == symbol_code:
                return position.quantity
        return Decimal("0")

    def get_latest_price(self, symbol_code: str) -> Decimal | None:
        """Return the latest cached price for a symbol."""
        return self.price_cache.get(symbol_code)
