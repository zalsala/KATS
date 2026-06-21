"""Immutable portfolio snapshot."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.domain.portfolio.cash_balance import CashBalance
from app.domain.portfolio.portfolio import Portfolio
from app.domain.portfolio.position import Position


@dataclass(frozen=True, slots=True)
class PortfolioSnapshot:
    """Read-only portfolio snapshot."""

    account_no: str
    cash: CashBalance
    positions: tuple[Position, ...]
    total_evaluation: Decimal
    total_purchase: Decimal
    total_profit_loss: Decimal
    total_asset: Decimal
    profit_rate: Decimal
    updated_at: datetime

    @classmethod
    def from_portfolio(cls, portfolio: Portfolio) -> PortfolioSnapshot:
        """Create a snapshot from a live portfolio."""
        return cls(
            account_no=portfolio.account_no,
            cash=portfolio.cash,
            positions=tuple(portfolio.positions.values()),
            total_evaluation=portfolio.total_evaluation,
            total_purchase=portfolio.total_purchase,
            total_profit_loss=portfolio.total_profit_loss,
            total_asset=portfolio.total_asset,
            profit_rate=portfolio.profit_rate,
            updated_at=portfolio.updated_at,
        )
