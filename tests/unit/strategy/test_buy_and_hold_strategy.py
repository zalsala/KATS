"""Buy and hold strategy tests."""

from __future__ import annotations

from decimal import Decimal

import pytest
from tests.fixtures.strategy_fixtures import register_and_start_strategy, sample_market_data_payload

from app.domain.strategy.trading_signal import SignalType
from app.service.strategy.strategy_service import StrategyService

pytestmark = pytest.mark.unit


def test_buy_and_hold_generates_single_buy_signal() -> None:
    service = StrategyService()
    strategy_id = register_and_start_strategy(
        service,
        strategy_type="buy_and_hold",
        name="buy-hold-1",
        parameters={"quantity": "2"},
    )

    results = service.handle_market_data(sample_market_data_payload(price="71000"))
    assert len(results) == 1
    assert results[0].accepted is True
    assert results[0].signal is not None
    assert results[0].signal.signal_type == SignalType.BUY
    assert results[0].signal.quantity == Decimal("2")

    second = service.handle_market_data(sample_market_data_payload(price="72000"))
    assert second == []

    managed = service.manager.get(strategy_id)
    assert managed is not None
    stats = managed.entity.statistics
    assert stats is not None
    assert stats.buy_signals == 1
