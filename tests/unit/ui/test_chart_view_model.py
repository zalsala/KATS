"""Chart view model tests."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.chart.in_memory_candle_store import InMemoryCandleStore
from app.service.chart.chart_service import ChartService
from app.ui.viewmodels.chart_view_model import DEFAULT_SYMBOL, ChartViewModel

pytestmark = pytest.mark.unit


def _seed_candles(service: ChartService, symbol: str = DEFAULT_SYMBOL) -> None:
    service.on_trade(symbol, "70000", 10, timestamp=datetime(2024, 6, 20, 12, 1, 3, tzinfo=UTC))
    service.on_trade(symbol, "70500", 5, timestamp=datetime(2024, 6, 20, 12, 1, 40, tzinfo=UTC))


def test_chart_view_model_refresh_loads_candles() -> None:
    service = ChartService(store=InMemoryCandleStore())
    _seed_candles(service)
    view_model = ChartViewModel(service, symbol_code=DEFAULT_SYMBOL)

    view_model.refresh()

    assert len(view_model.candles) == 1
    assert view_model.candles[0].close == Decimal("70500")


def test_chart_view_model_refresh_notifies_listeners() -> None:
    service = ChartService(store=InMemoryCandleStore())
    _seed_candles(service)
    view_model = ChartViewModel(service)
    changes: list[str] = []
    view_model.add_listener(lambda field: changes.append(field))

    view_model.refresh()

    assert changes == ["candles"]


def test_chart_view_model_set_symbol() -> None:
    service = ChartService(store=InMemoryCandleStore())
    _seed_candles(service, symbol="005930")
    service.on_trade("000660", "120000", 2, timestamp=datetime(2024, 6, 20, 12, 2, 0, tzinfo=UTC))
    view_model = ChartViewModel(service, symbol_code="005930")

    view_model.set_symbol("000660")

    assert view_model.symbol_code == "000660"
    assert view_model.candles[0].symbol == "000660"


def test_chart_view_model_refresh_updates_diagnostics() -> None:
    service = ChartService(store=InMemoryCandleStore())
    _seed_candles(service)
    view_model = ChartViewModel(service, symbol_code=DEFAULT_SYMBOL)

    view_model.refresh()

    assert view_model.total_ticks_received == 2
    assert view_model.total_candles == 1
    assert view_model.last_trade_symbol == DEFAULT_SYMBOL
    assert view_model.last_trade_price == "70500"
    assert view_model.last_trade_time
