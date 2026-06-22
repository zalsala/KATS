"""Chart interaction tests."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QPoint, QRect
from PySide6.QtWidgets import QApplication

from app.chart.candle import Candle
from app.chart.in_memory_candle_store import InMemoryCandleStore
from app.chart.timeframe import Timeframe
from app.indicator.indicator_service import (
    ema_indicator_name,
    sma_indicator_name,
)
from app.service.chart.chart_service import build_chart_service
from app.ui.chart.candle_inspector import candle_index_at_x
from app.ui.chart.chart_layout import plot_rect
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
        open=price - Decimal("1"),
        high=price + Decimal("2"),
        low=price - Decimal("2"),
        close=price,
        volume=1000 + minute,
    )


def _seed_candles(service, count: int = 25) -> None:
    for minute in range(1, count + 1):
        service.on_trade(
            DEFAULT_SYMBOL,
            str(100 + minute),
            10,
            timestamp=datetime(2024, 6, 20, 12, minute, 0, tzinfo=UTC),
        )


def test_crosshair_hidden_outside_plot_area(qapp) -> None:
    widget = ChartWidget()
    widget.resize(640, 320)
    widget.set_candles([_candle(1, "100"), _candle(2, "110")], symbol=DEFAULT_SYMBOL)
    widget.show()
    qapp.processEvents()

    widget._update_hover_at(QPoint(4, 4))  # noqa: SLF001
    qapp.processEvents()
    assert widget.hover_state.active is False
    assert widget.crosshair.isVisible() is False


def test_crosshair_visible_inside_plot_area(qapp) -> None:
    widget = ChartWidget()
    widget.resize(640, 320)
    candles = [_candle(minute, str(100 + minute)) for minute in range(1, 11)]
    widget.set_candles(candles, symbol=DEFAULT_SYMBOL)
    widget.show()
    qapp.processEvents()

    plot_area = plot_rect(widget.rect())
    hover_point = QPoint(plot_area.center().x(), plot_area.center().y())
    widget._update_hover_at(hover_point)  # noqa: SLF001
    qapp.processEvents()

    assert widget.hover_state.active is True
    assert widget.crosshair.isVisible() is True
    assert widget.crosshair.hover_state.cursor_x == hover_point.x()


def test_hover_candle_selection(qapp) -> None:
    widget = ChartWidget()
    widget.resize(640, 320)
    candles = [_candle(minute, str(100 + minute)) for minute in range(1, 6)]
    widget.set_candles(candles, symbol=DEFAULT_SYMBOL)
    widget.show()
    qapp.processEvents()

    plot_area = plot_rect(widget.rect())
    slot_width = plot_area.width() / len(candles)
    hover_point = QPoint(plot_area.left() + int(slot_width * 3.5), plot_area.center().y())
    widget._update_hover_at(hover_point)  # noqa: SLF001

    assert widget.hover_state.candle_index == 3
    assert widget.hover_state.inspection is not None
    assert widget.hover_state.inspection.candle == candles[3]


def test_ohlc_data_displayed_in_tooltip(qapp) -> None:
    candle = _candle(5, "105")
    widget = ChartWidget()
    widget.resize(640, 320)
    widget.set_candles([candle], symbol=DEFAULT_SYMBOL)
    widget.show()
    qapp.processEvents()

    plot_area = plot_rect(widget.rect())
    widget._update_hover_at(plot_area.center())  # noqa: SLF001
    qapp.processEvents()

    inspection = widget.hover_tooltip.inspection
    assert inspection is not None
    assert inspection.timestamp_line == "2024-06-20 12:05"
    assert inspection.ohlc_lines == (
        "O: 104",
        "H: 107",
        "L: 103",
        "C: 105",
        "V: 1,005",
    )
    assert widget.hover_tooltip.isVisible() is True


def test_indicator_values_displayed_from_series(qapp) -> None:
    candles = [_candle(minute, str(100 + minute)) for minute in range(1, 6)]
    series = {
        sma_indicator_name(20): [
            (candles[2].timestamp, Decimal("101.2")),
            (candles[4].timestamp, Decimal("103.4")),
        ],
        ema_indicator_name(20): [(candles[4].timestamp, Decimal("101.8"))],
    }

    widget = ChartWidget()
    widget.resize(640, 320)
    widget.set_candles(candles, symbol=DEFAULT_SYMBOL)
    widget.set_indicator_series(series)
    widget.show()
    qapp.processEvents()

    plot_area = plot_rect(widget.rect())
    slot_width = plot_area.width() / len(candles)
    hover_point = QPoint(plot_area.left() + int(slot_width * 4.5), plot_area.center().y())
    widget._update_hover_at(hover_point)  # noqa: SLF001

    lines = widget.hover_tooltip.inspection.indicator_lines  # type: ignore[union-attr]
    assert len(lines) == 2
    assert lines[0].label == "SMA(20)"
    assert lines[0].formatted_value == "103.4"
    assert lines[1].label == "EMA(20)"
    assert lines[1].formatted_value == "101.8"


def test_disabled_indicators_hidden_from_tooltip(qapp) -> None:
    service = build_chart_service(store=InMemoryCandleStore())
    _seed_candles(service)

    view_model = ChartViewModel(service, symbol_code=DEFAULT_SYMBOL)
    view_model.refresh()
    view_model.update_indicator_settings(
        IndicatorSettings(sma_enabled=True, ema_enabled=False, vwap_enabled=False),
    )

    widget = ChartWidget()
    widget.resize(640, 320)
    widget.set_candles(view_model.candles, symbol=view_model.symbol_code)
    widget.set_indicator_series(view_model.indicator_series)
    widget.show()
    qapp.processEvents()

    plot_area = plot_rect(widget.rect())
    widget._update_hover_at(plot_area.center())  # noqa: SLF001

    inspection = widget.hover_tooltip.inspection
    assert inspection is not None
    assert all(line.label.startswith("SMA") for line in inspection.indicator_lines)
    assert not any(line.label.startswith("EMA") for line in inspection.indicator_lines)


def test_realtime_update_preserves_hover_inspection(qapp) -> None:
    service = build_chart_service(store=InMemoryCandleStore())
    view_model = ChartViewModel(service, symbol_code=DEFAULT_SYMBOL)
    widget = ChartWidget()
    widget.resize(640, 320)

    _seed_candles(service, count=22)
    view_model.refresh()
    widget.set_candles(view_model.candles, symbol=view_model.symbol_code)
    widget.set_indicator_series(view_model.indicator_series)
    widget.show()
    qapp.processEvents()

    plot_area = plot_rect(widget.rect())
    slot_width = plot_area.width() / len(view_model.candles)
    hover_point = QPoint(
        plot_area.left() + int(slot_width * (len(view_model.candles) - 0.5)),
        plot_area.center().y(),
    )
    widget._update_hover_at(hover_point)  # noqa: SLF001
    assert widget.crosshair.isVisible() is True
    assert widget.hover_tooltip.inspection is not None
    assert widget.hover_tooltip.inspection.indicator_lines
    value_before = widget.hover_tooltip.inspection.indicator_lines[0].formatted_value

    service.on_trade(
        DEFAULT_SYMBOL,
        "250",
        10,
        timestamp=datetime(2024, 6, 20, 12, 23, 0, tzinfo=UTC),
    )
    view_model.refresh()
    widget.set_candles(view_model.candles, symbol=view_model.symbol_code)
    widget.set_indicator_series(view_model.indicator_series)
    qapp.processEvents()

    assert widget.crosshair.isVisible() is True
    assert widget.hover_tooltip.isVisible() is True
    value_after = widget.hover_tooltip.inspection.indicator_lines[0].formatted_value  # type: ignore[union-attr]
    assert value_after != value_before


def test_timeframe_switch_updates_hover_data(qapp) -> None:
    service = build_chart_service(store=InMemoryCandleStore())
    view_model = ChartViewModel(service, symbol_code=DEFAULT_SYMBOL)
    view_model.update_indicator_settings(IndicatorSettings(sma_enabled=True, sma_period=5))

    widget = ChartWidget()
    widget.resize(640, 320)
    _seed_candles(service, count=30)
    view_model.refresh()
    widget.set_candles(view_model.candles, symbol=view_model.symbol_code)
    widget.set_indicator_series(view_model.indicator_series)
    widget.show()
    qapp.processEvents()

    plot_area = plot_rect(widget.rect())
    widget._update_hover_at(plot_area.center())  # noqa: SLF001
    interval_1m = widget.hover_tooltip.inspection.candle.interval  # type: ignore[union-attr]

    view_model.set_timeframe(Timeframe.M5)
    widget.set_candles(view_model.candles, symbol=view_model.symbol_code)
    widget.set_indicator_series(view_model.indicator_series)
    widget._update_hover_at(plot_area.center())  # noqa: SLF001
    qapp.processEvents()

    inspection = widget.hover_tooltip.inspection
    assert inspection is not None
    assert inspection.candle.interval == "5m"
    assert inspection.candle.interval != interval_1m


def test_candle_inspector_index_resolution() -> None:
    plot_area = QRect(56, 12, 500, 200)
    assert candle_index_at_x(56, plot_area, 10) == 0
    assert candle_index_at_x(305, plot_area, 10) == 4
    assert candle_index_at_x(20, plot_area, 10) is None


def test_market_view_chart_supports_hover(qapp) -> None:
    service = build_chart_service(store=InMemoryCandleStore())
    _seed_candles(service)

    view_model = MainViewModel(chart_service=service)
    controller = UiController(context=MagicMock())
    view = MarketView(view_model=view_model, controller=controller)
    view.show()
    qapp.processEvents()

    chart = view.chart_widget
    plot_area = plot_rect(chart.rect())
    chart._update_hover_at(plot_area.center())  # noqa: SLF001
    qapp.processEvents()

    assert chart.hover_tooltip.inspection is not None
    assert chart.crosshair.isVisible() is True
