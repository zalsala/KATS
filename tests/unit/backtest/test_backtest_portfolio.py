"""Backtest portfolio sync tests."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.backtest.backtest_portfolio import BacktestPortfolio
from app.portfolio.portfolio_engine import BUY_SIDE
from app.service.portfolio.portfolio_service import PortfolioService

pytestmark = pytest.mark.unit


def test_backtest_portfolio_syncs_cash_and_position() -> None:
    service = PortfolioService(account_no="backtest")
    portfolio = BacktestPortfolio(portfolio_service=service)
    portfolio.initialize(initial_capital=Decimal("1000000"))

    portfolio.apply_virtual_fill(
        {
            "symbol_code": "005930",
            "side": BUY_SIDE,
            "executed_quantity": "1",
            "executed_price": "70000",
        }
    )

    snapshot = portfolio.get_snapshot()
    assert snapshot.cash.orderable_cash == Decimal("930000")
    assert snapshot.positions[0].quantity == Decimal("1")

    portfolio.apply_market_data({"symbol_code": "005930", "price": "80000"})
    updated = portfolio.get_snapshot()
    assert updated.total_evaluation == Decimal("80000")
