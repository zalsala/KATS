"""Backtest portfolio wrapper."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.domain.portfolio.portfolio_snapshot import PortfolioSnapshot
from app.portfolio.portfolio_engine import BUY_SIDE, SELL_SIDE
from app.service.portfolio.portfolio_service import PortfolioService


class BacktestPortfolio:
    """Virtual portfolio for backtests with cash-aware fills."""

    def __init__(self, *, portfolio_service: PortfolioService) -> None:
        self._service = portfolio_service

    def initialize(
        self, *, initial_capital: Decimal, account_no: str = "backtest"
    ) -> PortfolioSnapshot:
        """Initialize portfolio with starting cash and no holdings."""
        return self._service.apply_account(
            {
                "account_no": account_no,
                "total_deposit": str(initial_capital),
                "orderable_cash": str(initial_capital),
                "holdings": [],
            }
        )

    def get_snapshot(self) -> PortfolioSnapshot:
        """Return current portfolio snapshot."""
        return self._service.get_snapshot()

    def apply_virtual_fill(self, payload: dict[str, Any]) -> PortfolioSnapshot:
        """Apply a virtual execution and adjust cash balance."""
        side = str(payload.get("side", ""))
        quantity = Decimal(str(payload.get("executed_quantity", "0")))
        price = Decimal(str(payload.get("executed_price", "0")))
        amount = quantity * price

        snapshot = self._service.apply_execution(payload)
        if side == BUY_SIDE:
            return self._service.engine.adjust_cash(-amount)
        if side == SELL_SIDE:
            return self._service.engine.adjust_cash(amount)
        return snapshot

    def apply_market_data(self, payload: dict[str, Any]) -> PortfolioSnapshot:
        """Update mark-to-market prices."""
        return self._service.apply_market_data(payload)
