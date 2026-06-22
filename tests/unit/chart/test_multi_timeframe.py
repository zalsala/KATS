"""Multi-timeframe chart tests."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.chart.candle_builder import CandleBuilder, bucket_start
from app.chart.in_memory_candle_store import InMemoryCandleStore
from app.chart.timeframe import Timeframe
from app.service.chart.chart_service import ChartService
from app.ui.viewmodels.chart_view_model import ChartViewModel

pytestmark = pytest.mark.unit

SYMBOL = "005930"


def _ts(hour: int = 12, minute: int = 0, second: int = 0) -> datetime:
    return datetime(2024, 6, 20, hour, minute, second, tzinfo=UTC)


def test_m1_bucket_generation() -> None:
    assert bucket_start(_ts(minute=3, second=15), Timeframe.M1) == _ts(minute=3)


def test_m5_bucket_generation() -> None:
    assert bucket_start(_ts(minute=3), Timeframe.M5) == _ts(minute=0)
    assert bucket_start(_ts(minute=7), Timeframe.M5) == _ts(minute=5)
    assert bucket_start(_ts(minute=12), Timeframe.M5) == _ts(minute=10)


def test_m15_bucket_generation() -> None:
    assert bucket_start(_ts(minute=10), Timeframe.M15) == _ts(minute=0)
    assert bucket_start(_ts(minute=20), Timeframe.M15) == _ts(minute=15)
    assert bucket_start(_ts(minute=45), Timeframe.M15) == _ts(minute=45)


def test_h1_bucket_generation() -> None:
    assert bucket_start(_ts(minute=30), Timeframe.H1) == _ts(minute=0)
    assert bucket_start(_ts(hour=13, minute=59), Timeframe.H1) == _ts(hour=13, minute=0)


def test_independent_candle_streams_per_timeframe() -> None:
    service = ChartService(store=InMemoryCandleStore())
    service.on_trade(SYMBOL, "70000", 10, timestamp=_ts(minute=1, second=5))
    service.on_trade(SYMBOL, "71000", 4, timestamp=_ts(minute=2, second=0))

    m1_candles = service.get_candles(SYMBOL, Timeframe.M1)
    m5_candles = service.get_candles(SYMBOL, Timeframe.M5)

    assert len(m1_candles) == 2
    assert len(m5_candles) == 1
    assert m1_candles[0].timestamp == _ts(minute=1)
    assert m5_candles[0].timestamp == _ts(minute=0)
    assert m5_candles[0].close == Decimal("71000")


def test_chart_service_timeframe_lookup() -> None:
    store = InMemoryCandleStore()
    service = ChartService(store=store)
    service.on_trade(SYMBOL, "70000", 10, timestamp=_ts(minute=14, second=50))
    service.on_trade(SYMBOL, "70500", 2, timestamp=_ts(minute=15, second=0))

    m1_stored = store.load_candles(SYMBOL, "1m")
    m15_candles = service.get_candles(SYMBOL, Timeframe.M15)

    assert len(m1_stored) == 1
    assert m1_stored[0].timestamp == _ts(minute=14)
    assert len(m15_candles) == 2
    assert m15_candles[0].timestamp == _ts(minute=0)
    assert m15_candles[-1].timestamp == _ts(minute=15)
    assert m15_candles[-1].volume == 2

    stats = service.get_chart_stats(SYMBOL, Timeframe.M15)
    assert stats["timeframe"] == "15m"
    assert stats["candles"] == 2


def test_view_model_timeframe_switching() -> None:
    service = ChartService(store=InMemoryCandleStore())
    service.on_trade(SYMBOL, "70000", 10, timestamp=_ts(minute=1, second=5))
    service.on_trade(SYMBOL, "71000", 4, timestamp=_ts(minute=2, second=0))
    view_model = ChartViewModel(service, symbol_code=SYMBOL, selected_timeframe=Timeframe.M1)

    view_model.refresh()
    assert len(view_model.candles) == 2
    assert view_model.selected_timeframe == Timeframe.M1

    view_model.set_timeframe(Timeframe.M5)
    assert view_model.selected_timeframe == Timeframe.M5
    assert len(view_model.candles) == 1
    assert view_model.candles[0].interval == "5m"


def test_builder_m5_finalizes_on_bucket_rollover() -> None:
    builder = CandleBuilder(SYMBOL, timeframe=Timeframe.M5)
    builder.update_trade("70000", 10, timestamp=_ts(minute=3))
    finalized = builder.update_trade("71000", 2, timestamp=_ts(minute=5))

    assert finalized is not None
    assert finalized.timestamp == _ts(minute=0)
    assert finalized.close == Decimal("70000")
    current = builder.get_current_candle()
    assert current is not None
    assert current.timestamp == _ts(minute=5)
    assert current.close == Decimal("71000")
