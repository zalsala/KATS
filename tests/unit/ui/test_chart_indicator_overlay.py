"""Chart indicator overlay tests."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QApplication

from app.chart.candle import Candle
from app.chart.in_memory_candle_store import InMemoryCandleStore
from app.indicator.indicator_service import (
    DEFAULT_EMA_NAME,
    DEFAULT_SMA_NAME,
    DEFAULT_VWAP_NAME,
    IndicatorService,
    ema_indicator_name,
    sma_indicator_name,
)
from app.service.chart.chart_service import build_chart_service
from app.ui.controllers.ui_controller import UiController
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


def _candle(minute: int, close: str) -> Candle:
    price = Decimal(close)
    return Candle(
        symbol=DEFAULT_SYMBOL,
        interval="1m",
        timestamp=datetime(2024, 6, 20, 12, minute, 0, tzinfo=UTC),
        open=price,
        high=price,
        low=price,
        close=price,
        volume=10,
    )


def test_chart_widget_accepts_indicator_series(qapp) -> None:
    widget = ChartWidget()
    candles = [_candle(1, "100"), _candle(2, "110"), _candle(3, "120")]
    series = {
        DEFAULT_SMA_NAME: [
            (candles[1].timestamp, Decimal("105")),
            (candles[2].timestamp, Decimal("115")),
        ]
    }

    widget.set_candles(candles, symbol=DEFAULT_SYMBOL)
    widget.set_indicator_series(series)

    assert widget.indicator_series[DEFAULT_SMA_NAME]
    assert len(widget.indicator_series[DEFAULT_SMA_NAME]) == 2


def test_chart_widget_empty_series_does_not_crash(qapp) -> None:
    widget = ChartWidget()
    widget.set_candles([_candle(1, "100")], symbol=DEFAULT_SYMBOL)
    widget.set_indicator_series({})
    widget.show()
    widget.repaint()
    qapp.processEvents()


def test_chart_widget_stores_multiple_series_independently(qapp) -> None:
    widget = ChartWidget()
    candles = [_candle(1, "100"), _candle(2, "110")]
    widget.set_candles(candles, symbol=DEFAULT_SYMBOL)
    widget.set_indicator_series(
        {
            DEFAULT_SMA_NAME: [(candles[1].timestamp, Decimal("105"))],
            DEFAULT_EMA_NAME: [(candles[1].timestamp, Decimal("108"))],
        }
    )

    assert set(widget.indicator_series) == {DEFAULT_SMA_NAME, DEFAULT_EMA_NAME}


def test_chart_view_model_exposes_indicator_series() -> None:
    service = build_chart_service(store=InMemoryCandleStore())
    for minute in range(1, 23):
        service.on_trade(
            DEFAULT_SYMBOL,
            str(100 + minute),
            10,
            timestamp=datetime(2024, 6, 20, 12, minute, 0, tzinfo=UTC),
        )

    view_model = ChartViewModel(service, symbol_code=DEFAULT_SYMBOL)
    view_model.refresh()

    assert sma_indicator_name(20) in view_model.indicator_series
    assert len(view_model.indicator_series[sma_indicator_name(20)]) >= 1


def test_market_view_checkbox_toggles_overlay_visibility(qapp) -> None:
    service = build_chart_service(store=InMemoryCandleStore())
    for minute in range(1, 23):
        service.on_trade(
            DEFAULT_SYMBOL,
            str(100 + minute),
            10,
            timestamp=datetime(2024, 6, 20, 12, minute, 0, tzinfo=UTC),
        )

    view_model = MainViewModel(chart_service=service)
    controller = UiController(context=MagicMock())
    view = MarketView(view_model=view_model, controller=controller)
    view.show()
    qapp.processEvents()

    assert view_model.chart.indicator_settings.sma_enabled is True
    assert sma_indicator_name(20) in view.chart_widget.indicator_series

    view._ema_checkbox.setChecked(True)  # noqa: SLF001
    qapp.processEvents()
    assert ema_indicator_name(20) in view.chart_widget.indicator_series

    view._sma_checkbox.setChecked(False)  # noqa: SLF001
    qapp.processEvents()
    assert sma_indicator_name(20) not in view.chart_widget.indicator_series


def test_paint_event_smoke_with_candles_and_indicators(qapp) -> None:
    widget = ChartWidget()
    candles = [_candle(minute, str(100 + minute)) for minute in range(1, 25)]
    indicator_service = IndicatorService()
    indicator_service.configure_overlay_indicators(
        DEFAULT_SYMBOL,
        "1m",
        sma_enabled=True,
        sma_period=20,
        ema_enabled=False,
        ema_period=20,
        vwap_enabled=True,
    )
    series = indicator_service.build_overlay_series(
        DEFAULT_SYMBOL,
        "1m",
        candles,
        names=(sma_indicator_name(20), DEFAULT_VWAP_NAME),
    )

    widget.resize(640, 320)
    widget.set_candles(candles, symbol=DEFAULT_SYMBOL)
    widget.set_indicator_series(series)
    widget.show()
    widget.repaint()
    qapp.processEvents()

    assert widget.indicator_series
