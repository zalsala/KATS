"""Virtual order executor tests."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.backtest.backtest_portfolio import BacktestPortfolio
from app.backtest.performance_analyzer import PerformanceAnalyzer
from app.backtest.virtual_order_executor import VirtualOrderExecutor
from app.service.portfolio.portfolio_service import PortfolioService

pytestmark = pytest.mark.unit


def test_virtual_order_executor_applies_buy_fill() -> None:
    portfolio_service = PortfolioService(account_no="backtest")
    portfolio = BacktestPortfolio(portfolio_service=portfolio_service)
    portfolio.initialize(initial_capital=Decimal("1000000"))
    analyzer = PerformanceAnalyzer(initial_capital=Decimal("1000000"))
    executor = VirtualOrderExecutor(portfolio=portfolio, analyzer=analyzer)

    executor.execute_approved_payload(
        {
            "status": "APPROVED",
            "approved": True,
            "signal_type": "BUY",
            "symbol_code": "005930",
            "price": "70000",
            "quantity": "2",
            "signal_id": "sig-1",
        }
    )

    snapshot = portfolio.get_snapshot()
    assert len(snapshot.positions) == 1
    assert snapshot.positions[0].quantity == Decimal("2")
    assert snapshot.cash.orderable_cash == Decimal("860000")
