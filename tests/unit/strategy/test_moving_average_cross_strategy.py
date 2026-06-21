"""Moving average cross strategy tests."""

from __future__ import annotations

import pytest
from tests.fixtures.strategy_fixtures import register_and_start_strategy, sample_market_data_payload

from app.domain.strategy.trading_signal import SignalType
from app.service.strategy.strategy_service import StrategyService

pytestmark = pytest.mark.unit


def test_moving_average_cross_generates_buy_on_golden_cross() -> None:
    service = StrategyService()
    register_and_start_strategy(
        service,
        strategy_type="moving_average_cross",
        name="ma-cross",
        parameters={"short_period": 2, "long_period": 3, "quantity": "1"},
    )

    prices = ["100", "100", "100", "110", "120", "130"]
    results = []
    for price in prices:
        batch = service.handle_market_data(sample_market_data_payload(price=price))
        results.extend(batch)

    buy_signals = [
        item for item in results if item.signal and item.signal.signal_type == SignalType.BUY
    ]
    assert buy_signals
