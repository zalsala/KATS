"""Strategy mapper tests."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.domain.strategy.strategy import Strategy
from app.domain.strategy.trading_signal import SignalType, TradingSignal
from app.dto.strategy.mappers.strategy_mappers import SignalMapper, StrategyMapper

pytestmark = pytest.mark.unit


def test_strategy_mapper_round_trip() -> None:
    entity = Strategy(
        strategy_id="s1",
        name="test",
        strategy_type="buy_and_hold",
        enabled=True,
        parameters={"quantity": "1"},
        symbols=("005930",),
    )
    dto = StrategyMapper.to_dto(entity)
    restored = StrategyMapper.to_entity(dto)
    assert restored.strategy_id == "s1"
    assert restored.symbols == ("005930",)


def test_signal_mapper_to_dto() -> None:
    signal = TradingSignal(
        signal_id="sig1",
        strategy_id="s1",
        strategy_name="test",
        symbol_code="005930",
        signal_type=SignalType.BUY,
        price=Decimal("70000"),
        quantity=Decimal("1"),
        confidence=Decimal("1"),
        timestamp=datetime.now(UTC),
    )
    dto = SignalMapper.to_dto(signal)
    assert dto.signal_type == "BUY"
    assert dto.price == "70000"
