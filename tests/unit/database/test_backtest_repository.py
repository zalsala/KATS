"""Backtest repository tests."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from tests.fixtures.database_fixtures import build_test_database_manager

from app.domain.backtest.backtest_result import BacktestResult

pytestmark = pytest.mark.unit


def test_backtest_repository_save_and_get(tmp_path) -> None:
    manager = build_test_database_manager(tmp_path)
    repository = manager.build_backtest_repository()
    result = BacktestResult(
        initial_capital=Decimal("1000000"),
        final_asset=Decimal("1100000"),
        total_return_rate=Decimal("0.1"),
        win_rate=Decimal("0.6"),
        profit_loss_ratio=Decimal("1.5"),
        profit_factor=Decimal("1.2"),
        max_drawdown=Decimal("0.05"),
        trade_count=3,
        average_profit=Decimal("10000"),
        average_loss=Decimal("5000"),
        equity_curve=((datetime(2024, 1, 1, tzinfo=UTC), Decimal("1000000")),),
    )
    result_id = repository.save(
        result,
        strategy_type="template",
        strategy_name="scheduled-backtest",
        symbols=["005930"],
    )
    loaded = repository.get(result_id)
    assert loaded is not None
    assert loaded.trade_count == 3
    assert repository.list_all()[0][0] == result_id
