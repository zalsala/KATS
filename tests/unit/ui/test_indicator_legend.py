"""Indicator legend overlay tests."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QApplication

from app.chart.candle import Candle
from app.chart.in_memory_candle_store import InMemoryCandleStore
from app.chart.timeframe import Timeframe
from app.indicator.indicator_display import (
    INDICATOR_COLOR_HEX,
    build_legend_items,
    format_indicator_label,
)
from app.indicator.indicator_service import (
    DEFAULT_VWAP_NAME,
    ema_indicator_name,
    sma_indicator_name,
)
from app.service.chart.chart_service import build_chart_service
from app.ui.controllers.ui_controller import UiController
from app.ui.models.indicator_settings import IndicatorSettings
from app.ui.viewmodels.chart_view_model import DEFAULT_SYMBOL, ChartViewModel
from app.ui.viewmodels.main_view_model import MainViewModel
from app.ui.views.market_view import MarketView
from app.ui.widgets.chart_widget import ChartWidget

pytestmark = pytest.mark.unit


@pytest.fixture(scope="module")
def qapp():
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def _candle(minute: int, close: str, *, interval: str = "1m") -> Candle:
    price = Decimal(close)
    return Candle(
        symbol=DEFAULT_SYMBOL,
        interval=interval,
        timestamp=datetime(2024, 6, 20, 12, minute, 0, tzinfo=UTC),
        open=price,
        high=price,
        low=price,
        close=price,
        volume=10,
    )


def _seed_candles(service, count: int = 25) -> None:
    for minute in range(1, count + 1):
        service.on_trade(
            DEFAULT_SYMBOL,
            str(100 + minute),
            10,
            timestamp=datetime(2024, 6, 20, 12, minute, 0, tzinfo=UTC),
        )


def test_build_legend_items_renders_enabled_indicators() -> None:
    candles = [_candle(1, "100"), _candle(2, "110"), _candle(3, "120")]
    series = {
        sma_indicator_name(20): [
            (candles[1].timestamp, Decimal("105")),
            (candles[2].timestamp, Decimal("115")),
        ],
        ema_indicator_name(9): [(candles[2].timestamp, Decimal("118"))],
    }

    items = build_legend_items(series)

    assert len(items) == 2
    assert items[0].label == "SMA(20)"
    assert items[1].label == "EMA(9)"
    assert items[0].color_hex == INDICATOR_COLOR_HEX["SMA"]
    assert items[1].color_hex == INDICATOR_COLOR_HEX["EMA"]


def test_disabled_indicators_are_not_shown() -> None:
    items = build_legend_items({})

    assert items == ()
    assert format_indicator_label(DEFAULT_VWAP_NAME) == "VWAP"


def test_latest_values_are_displayed(qapp) -> None:
    widget = ChartWidget()
    candles = [_candle(minute, str(100 + minute)) for minute in range(1, 25)]
    latest_value = Decimal("124")
    series = {
        sma_indicator_name(20): [
            (candles[-2].timestamp, Decimal("123")),
            (candles[-1].timestamp, latest_value),
        ]
    }

    widget.resize(640, 320)
    widget.set_candles(candles, symbol=DEFAULT_SYMBOL)
    widget.set_indicator_series(series)
    widget.show()
    qapp.processEvents()

    legend = widget.indicator_legend
    assert legend.isVisible() is True
    assert len(legend.items) == 1
    assert legend.items[0].latest_value == latest_value
    assert legend.items[0].formatted_value == "124"


def test_legend_updates_when_candle_data_changes(qapp) -> None:
    service = build_chart_service(store=InMemoryCandleStore())
    view_model = ChartViewModel(service, symbol_code=DEFAULT_SYMBOL)
    widget = ChartWidget()
    widget.resize(640, 320)

    _seed_candles(service, count=22)
    view_model.refresh()
    widget.set_candles(view_model.candles, symbol=view_model.symbol_code)
    widget.set_indicator_series(view_model.indicator_series)
    qapp.processEvents()

    first_value = widget.indicator_legend.items[0].latest_value

    service.on_trade(
        DEFAULT_SYMBOL,
        "200",
        10,
        timestamp=datetime(2024, 6, 20, 12, 23, 0, tzinfo=UTC),
    )
    view_model.refresh()
    widget.set_candles(view_model.candles, symbol=view_model.symbol_code)
    widget.set_indicator_series(view_model.indicator_series)
    qapp.processEvents()

    second_value = widget.indicator_legend.items[0].latest_value
    assert second_value != first_value


def test_legend_updates_when_timeframe_changes(qapp) -> None:
    service = build_chart_service(store=InMemoryCandleStore())
    view_model = ChartViewModel(service, symbol_code=DEFAULT_SYMBOL)
    view_model.update_indicator_settings(IndicatorSettings(sma_enabled=True, sma_period=5))
    widget = ChartWidget()
    widget.resize(640, 320)
    widget.show()

    _seed_candles(service, count=30)
    view_model.refresh()
    widget.set_candles(view_model.candles, symbol=view_model.symbol_code)
    widget.set_indicator_series(view_model.indicator_series)
    qapp.processEvents()

    value_1m = widget.indicator_legend.items[0].latest_value

    view_model.set_timeframe(Timeframe.M5)
    widget.set_candles(view_model.candles, symbol=view_model.symbol_code)
    widget.set_indicator_series(view_model.indicator_series)
    qapp.processEvents()

    assert view_model.selected_timeframe == Timeframe.M5
    assert widget.indicator_legend.isVisible() is True
    assert widget.indicator_legend.items[0].label == "SMA(5)"
    assert widget.indicator_legend.items[0].latest_value != value_1m


def test_no_legend_when_all_indicators_disabled(qapp) -> None:
    service = build_chart_service(store=InMemoryCandleStore())
    _seed_candles(service)

    view_model = ChartViewModel(service, symbol_code=DEFAULT_SYMBOL)
    view_model.refresh()
    view_model.update_indicator_settings(
        IndicatorSettings(sma_enabled=False, ema_enabled=False, vwap_enabled=False),
    )

    widget = ChartWidget()
    widget.resize(640, 320)
    widget.set_candles(view_model.candles, symbol=view_model.symbol_code)
    widget.set_indicator_series(view_model.indicator_series)
    widget.show()
    qapp.processEvents()

    assert view_model.indicator_series == {}
    assert widget.indicator_legend.isVisible() is False
    assert widget.indicator_legend.items == ()


def test_market_view_indicator_settings_control_legend(qapp) -> None:
    service = build_chart_service(store=InMemoryCandleStore())
    _seed_candles(service)

    view_model = MainViewModel(chart_service=service)
    controller = UiController(context=MagicMock())
    view = MarketView(view_model=view_model, controller=controller)
    view.show()
    qapp.processEvents()

    legend = view.chart_widget.indicator_legend
    assert legend.isVisible() is True
    assert any(item.label == "SMA(20)" for item in legend.items)

    view._ema_checkbox.setChecked(True)  # noqa: SLF001
    qapp.processEvents()
    labels = {item.label for item in legend.items}
    assert "SMA(20)" in labels
    assert "EMA(20)" in labels

    view._sma_checkbox.setChecked(False)  # noqa: SLF001
    qapp.processEvents()
    labels = {item.label for item in legend.items}
    assert "SMA(20)" not in labels
    assert "EMA(20)" in labels

    view._vwap_checkbox.setChecked(True)  # noqa: SLF001
    qapp.processEvents()
    labels = {item.label for item in legend.items}
    assert "VWAP" in labels
