"""ChartService tests."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.chart.in_memory_candle_store import InMemoryCandleStore
from app.service.chart.chart_service import ChartService

pytestmark = pytest.mark.unit


def _ts(minute: int, second: int = 0) -> datetime:
    return datetime(2024, 6, 20, 12, minute, second, tzinfo=UTC)


def test_volume_accumulates_within_minute() -> None:
    service = ChartService(store=InMemoryCandleStore())
    service.on_trade("005930", "70000", 10, timestamp=_ts(1, 3))
    service.on_trade("005930", "70100", 7, timestamp=_ts(1, 20))

    current = service.get_candles("005930")[0]

    assert current.volume == 17
    assert current.close == Decimal("70100")


def test_next_minute_persists_previous_candle() -> None:
    store = InMemoryCandleStore()
    service = ChartService(store=store)
    service.on_trade("005930", "70000", 10, timestamp=_ts(1, 50))
    service.on_trade("005930", "71000", 3, timestamp=_ts(2, 0))

    stored = store.load_candles("005930", "1m")
    current = service.get_candles("005930", include_current=True)[-1]

    assert len(stored) == 1
    assert stored[0].timestamp == _ts(1)
    assert stored[0].volume == 10
    assert current.timestamp == _ts(2)
    assert current.volume == 3


def test_symbols_are_isolated() -> None:
    service = ChartService(store=InMemoryCandleStore())
    service.on_trade("005930", "70000", 10, timestamp=_ts(1, 5))
    service.on_trade("000660", "120000", 4, timestamp=_ts(1, 8))

    samsung = service.get_candles("005930")[0]
    hynix = service.get_candles("000660")[0]

    assert samsung.symbol == "005930"
    assert samsung.close == Decimal("70000")
    assert hynix.symbol == "000660"
    assert hynix.close == Decimal("120000")


def test_get_candles_returns_stored_and_current() -> None:
    store = InMemoryCandleStore()
    service = ChartService(store=store)
    service.on_trade("005930", "70000", 10, timestamp=_ts(1, 10))
    service.on_trade("005930", "71000", 2, timestamp=_ts(2, 5))

    candles = service.get_candles("005930")

    assert len(candles) == 2
    assert candles[0].timestamp == _ts(1)
    assert candles[1].timestamp == _ts(2)


def test_finalize_symbol_persists_in_progress_candle() -> None:
    store = InMemoryCandleStore()
    service = ChartService(store=store)
    service.on_trade("005930", "70000", 10, timestamp=_ts(1, 10))

    finalized = service.finalize_symbol("005930")

    assert finalized is not None
    assert len(store.load_candles("005930", "1m")) == 1
    assert service.get_candles("005930", include_current=False) == store.load_candles(
        "005930",
        "1m",
    )


def test_get_chart_stats_tracks_ticks_and_candles() -> None:
    service = ChartService(store=InMemoryCandleStore())
    service.on_trade("005930", "70000", 10, timestamp=_ts(1, 3))
    service.on_trade("005930", "70500", 5, timestamp=_ts(1, 40))
    service.on_trade("005930", "71000", 3, timestamp=_ts(2, 0))

    symbol_stats = service.get_chart_stats("005930")
    global_stats = service.get_chart_stats()

    assert symbol_stats["ticks"] == 3
    assert symbol_stats["candles"] == 2
    assert symbol_stats["symbols"] == 1
    assert symbol_stats["last_symbol"] == "005930"
    assert symbol_stats["last_price"] == "71000"
    assert symbol_stats["last_trade_time"] == _ts(2, 0).isoformat()
    assert global_stats["ticks"] == 3
    assert global_stats["candles"] == 2
