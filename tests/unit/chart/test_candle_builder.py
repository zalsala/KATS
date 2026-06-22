"""CandleBuilder tests."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.chart.candle_builder import CandleBuilder

pytestmark = pytest.mark.unit


def _ts(minute: int, second: int = 0) -> datetime:
    return datetime(2024, 6, 20, 12, minute, second, tzinfo=UTC)


def test_first_trade_creates_current_candle() -> None:
    builder = CandleBuilder("005930")

    finalized = builder.update_trade("70000", 10, timestamp=_ts(1, 3))
    current = builder.get_current_candle()

    assert finalized is None
    assert current is not None
    assert current.timestamp == _ts(1)
    assert current.open == Decimal("70000")
    assert current.high == Decimal("70000")
    assert current.low == Decimal("70000")
    assert current.close == Decimal("70000")
    assert current.volume == 10


def test_same_minute_updates_high_low_close() -> None:
    builder = CandleBuilder("005930")
    builder.update_trade("70000", 10, timestamp=_ts(1, 3))

    builder.update_trade("70500", 5, timestamp=_ts(1, 10))
    builder.update_trade("69800", 2, timestamp=_ts(1, 50))
    current = builder.get_current_candle()

    assert current is not None
    assert current.open == Decimal("70000")
    assert current.high == Decimal("70500")
    assert current.low == Decimal("69800")
    assert current.close == Decimal("69800")
    assert current.volume == 17


def test_next_minute_finalizes_previous_candle() -> None:
    builder = CandleBuilder("005930")
    builder.update_trade("70000", 10, timestamp=_ts(1, 50))

    finalized = builder.update_trade("71000", 3, timestamp=_ts(2, 0))
    current = builder.get_current_candle()

    assert finalized is not None
    assert finalized.timestamp == _ts(1)
    assert finalized.close == Decimal("70000")
    assert finalized.volume == 10
    assert current is not None
    assert current.timestamp == _ts(2)
    assert current.open == Decimal("71000")


def test_finalize_returns_current_candle() -> None:
    builder = CandleBuilder("005930")
    builder.update_trade("70000", 4, timestamp=_ts(1, 15))

    finalized = builder.finalize()

    assert finalized is not None
    assert finalized.volume == 4
    assert builder.get_current_candle() is None
