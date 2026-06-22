"""Chart widget tests."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from PySide6.QtWidgets import QApplication

from app.chart.candle import Candle
from app.chart.in_memory_candle_store import InMemoryCandleStore
from app.service.chart.chart_service import ChartService
from app.ui.viewmodels.chart_view_model import DEFAULT_SYMBOL
from app.ui.viewmodels.main_view_model import MainViewModel
from app.ui.views.market_view import MarketView
from app.ui.widgets.chart_widget import EMPTY_MESSAGE, ChartWidget

pytestmark = pytest.mark.unit


@pytest.fixture(scope="module")
def qapp():
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def _sample_candle() -> Candle:
    return Candle(
        symbol=DEFAULT_SYMBOL,
        interval="1m",
        timestamp=datetime(2024, 6, 20, 12, 1, tzinfo=UTC),
        open=Decimal("70000"),
        high=Decimal("70500"),
        low=Decimal("69800"),
        close=Decimal("70400"),
        volume=15,
    )


def test_chart_widget_empty_state(qapp) -> None:
    widget = ChartWidget()

    assert widget.is_empty is True

    widget.show()
    qapp.processEvents()
    widget.repaint()
    qapp.processEvents()

    assert widget.isVisible()


def test_chart_widget_set_candles(qapp) -> None:
    widget = ChartWidget()

    widget.set_candles([_sample_candle()], symbol=DEFAULT_SYMBOL)

    assert widget.is_empty is False
    assert widget.symbol == DEFAULT_SYMBOL


def test_chart_widget_paint_event_smoke(qapp) -> None:
    widget = ChartWidget()
    widget.resize(640, 320)
    widget.set_candles([_sample_candle()], symbol=DEFAULT_SYMBOL)
    widget.show()
    widget.repaint()
    qapp.processEvents()

    assert widget.is_empty is False


def test_market_view_embeds_chart_widget(qapp) -> None:
    service = ChartService(store=InMemoryCandleStore())
    service.on_trade(
        DEFAULT_SYMBOL,
        "70000",
        10,
        timestamp=datetime(2024, 6, 20, 12, 1, 5, tzinfo=UTC),
    )
    view_model = MainViewModel(chart_service=service)
    view = MarketView(view_model=view_model)
    view.show()
    qapp.processEvents()

    assert isinstance(view.chart_widget, ChartWidget)
    assert view.chart_widget.is_empty is False
    assert view.chart_widget.symbol == DEFAULT_SYMBOL


def test_chart_widget_empty_message_constant() -> None:
    assert EMPTY_MESSAGE == "No chart data available"
