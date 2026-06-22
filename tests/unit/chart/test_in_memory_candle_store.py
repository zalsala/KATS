"""InMemoryCandleStore tests."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.chart.candle import Candle
from app.chart.in_memory_candle_store import InMemoryCandleStore

pytestmark = pytest.mark.unit


def _candle(symbol: str, minute: int) -> Candle:
    return Candle(
        symbol=symbol,
        interval="1m",
        timestamp=datetime(2024, 6, 20, 12, minute, tzinfo=UTC),
        open=Decimal("100"),
        high=Decimal("110"),
        low=Decimal("90"),
        close=Decimal("105"),
        volume=minute,
    )


def test_save_and_load_candles_sorted() -> None:
    store = InMemoryCandleStore()
    store.save_candle(_candle("005930", 2))
    store.save_candle(_candle("005930", 1))

    candles = store.load_candles("005930", "1m")

    assert [candle.timestamp.minute for candle in candles] == [1, 2]


def test_load_candles_respects_limit() -> None:
    store = InMemoryCandleStore()
    for minute in range(1, 4):
        store.save_candle(_candle("005930", minute))

    candles = store.load_candles("005930", "1m", limit=2)

    assert [candle.timestamp.minute for candle in candles] == [2, 3]
