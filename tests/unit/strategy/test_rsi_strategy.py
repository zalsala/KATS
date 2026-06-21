"""RSI strategy tests."""

from __future__ import annotations

import pytest
from tests.fixtures.strategy_fixtures import register_and_start_strategy, sample_market_data_payload

from app.domain.strategy.trading_signal import SignalType
from app.service.strategy.strategy_service import StrategyService

pytestmark = pytest.mark.unit


def test_rsi_strategy_generates_buy_on_oversold() -> None:
    service = StrategyService()
    register_and_start_strategy(
        service,
        strategy_type="rsi",
        name="rsi-1",
        parameters={"period": 3, "buy_threshold": "80", "sell_threshold": "90", "quantity": "1"},
    )

    prices = ["100", "99", "98", "97", "96", "95"]
    results = []
    for price in prices:
        batch = service.handle_market_data(sample_market_data_payload(price=price))
        results.extend(batch)

    buy_signals = [
        item for item in results if item.signal and item.signal.signal_type == SignalType.BUY
    ]
    assert buy_signals
