"""Performance analyzer tests."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.backtest.performance_analyzer import PerformanceAnalyzer

pytestmark = pytest.mark.unit


def test_performance_analyzer_metrics() -> None:
    analyzer = PerformanceAnalyzer(initial_capital=Decimal("1000000"))
    timestamp = datetime(2024, 1, 1, tzinfo=UTC)

    analyzer.record_equity(timestamp, Decimal("1000000"))
    analyzer.record_equity(timestamp, Decimal("1100000"))
    analyzer.record_trade(
        symbol_code="005930",
        side="01",
        quantity=Decimal("1"),
        price=Decimal("75000"),
        timestamp=timestamp,
        realized_pnl=Decimal("5000"),
    )
    analyzer.record_trade(
        symbol_code="005930",
        side="01",
        quantity=Decimal("1"),
        price=Decimal("70000"),
        timestamp=timestamp,
        realized_pnl=Decimal("-2000"),
    )

    result = analyzer.finalize(Decimal("1100000"))

    assert result.total_return_rate == Decimal("10")
    assert result.trade_count == 2
    assert result.win_rate == Decimal("50")
    assert result.average_profit == Decimal("5000")
    assert result.average_loss == Decimal("2000")
    assert result.profit_factor == Decimal("2.5")
