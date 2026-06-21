"""Strategy backtest integration tests."""

from __future__ import annotations

from decimal import Decimal

import pytest
from tests.fixtures.backtest_fixtures import build_permissive_risk_policy, build_sample_provider

from app.service.backtest.backtest_service import BacktestService

pytestmark = pytest.mark.unit


def test_buy_and_hold_strategy_backtest() -> None:
    service = BacktestService()
    result = service.run_backtest(
        provider=build_sample_provider(),
        strategy_type="buy_and_hold",
        strategy_name="bt-buy-hold",
        symbols=["005930"],
        parameters={"quantity": "1"},
        initial_capital=Decimal("1000000"),
        risk_policy=build_permissive_risk_policy(),
    )

    assert result.final_asset > result.initial_capital
    assert result.total_return_rate > Decimal("0")
    assert len(result.equity_curve) == 5
