"""Backtest trigger tests."""

from __future__ import annotations

from decimal import Decimal

import pytest
from tests.fixtures.ui_fixtures import build_test_ui_controller

from app.backtest.sample_data import build_sample_price_provider
from app.ui.viewmodels.backtest_view_model import BacktestViewModel

pytestmark = pytest.mark.unit


def test_backtest_trigger_updates_view_model() -> None:
    controller = build_test_ui_controller()
    vm = BacktestViewModel()
    result = controller.run_backtest(
        provider=build_sample_price_provider(),
        strategy_type="buy_and_hold",
        strategy_name="ui-test",
        symbols=["005930"],
        parameters={"quantity": "1"},
        initial_capital=Decimal("1000000"),
    )
    display = controller.to_backtest_display(result)
    vm.set_result(display, message="done")
    assert vm.last_result is not None
    assert vm.last_result.total_return_rate > Decimal("0")
