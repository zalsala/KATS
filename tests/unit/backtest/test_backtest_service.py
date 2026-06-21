"""BacktestService tests."""

from __future__ import annotations

from decimal import Decimal

import pytest
from tests.fixtures.backtest_fixtures import build_permissive_risk_policy, build_sample_provider

from app.service.backtest.backtest_service import build_backtest_service

pytestmark = pytest.mark.unit


def test_backtest_service_runs_with_default_capital() -> None:
    service = build_backtest_service()
    result = service.run_backtest(
        provider=build_sample_provider(),
        strategy_type="buy_and_hold",
        strategy_name="service-test",
        symbols=["005930"],
        parameters={"quantity": "1"},
        risk_policy=build_permissive_risk_policy(),
    )

    assert result.initial_capital == Decimal("10000000")
    assert result.final_asset > Decimal("0")
