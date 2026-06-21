"""Signal generator and evaluator tests."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.domain.strategy.trading_signal import SignalType
from app.strategy.signal_evaluator import SignalEvaluator
from app.strategy.signal_generator import SignalGenerator
from app.strategy.strategy_context import StrategyContext

pytestmark = pytest.mark.unit


def test_signal_generator_creates_signal() -> None:
    generator = SignalGenerator()
    signal = generator.create(
        strategy_id="s1",
        strategy_name="test",
        symbol_code="005930",
        signal_type=SignalType.BUY,
        price=Decimal("70000"),
        quantity=Decimal("1"),
    )
    assert signal.signal_id
    assert signal.signal_type == SignalType.BUY
    assert signal.price == Decimal("70000")


def test_signal_evaluator_accepts_valid_buy() -> None:
    generator = SignalGenerator()
    evaluator = SignalEvaluator()
    context = StrategyContext(
        strategy_id="s1",
        strategy_name="test",
        symbols=("005930",),
        parameters={},
    )
    signal = generator.create(
        strategy_id="s1",
        strategy_name="test",
        symbol_code="005930",
        signal_type=SignalType.BUY,
        price=Decimal("70000"),
        quantity=Decimal("1"),
    )
    result = evaluator.evaluate(signal, context=context)
    assert result.accepted is True


def test_signal_evaluator_rejects_unknown_symbol() -> None:
    generator = SignalGenerator()
    evaluator = SignalEvaluator()
    context = StrategyContext(
        strategy_id="s1",
        strategy_name="test",
        symbols=("005930",),
        parameters={},
    )
    signal = generator.create(
        strategy_id="s1",
        strategy_name="test",
        symbol_code="000660",
        signal_type=SignalType.BUY,
        price=Decimal("70000"),
        quantity=Decimal("1"),
    )
    result = evaluator.evaluate(signal, context=context)
    assert result.accepted is False
    assert result.message == "symbol_not_subscribed"
