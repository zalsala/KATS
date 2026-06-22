"""Market view realtime diagnostics tests."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QApplication

from app.chart.in_memory_candle_store import InMemoryCandleStore
from app.service.chart.chart_service import ChartService
from app.ui.controllers.ui_controller import UiController
from app.ui.viewmodels.chart_view_model import DEFAULT_SYMBOL
from app.ui.viewmodels.main_view_model import MainViewModel
from app.ui.views.market_view import MarketView

pytestmark = pytest.mark.unit


@pytest.fixture(scope="module")
def qapp():
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def test_market_view_shows_realtime_diagnostics(qapp) -> None:
    service = ChartService(store=InMemoryCandleStore())
    service.on_trade(
        DEFAULT_SYMBOL,
        "70100",
        4,
        timestamp=datetime(2024, 6, 20, 12, 1, 10, tzinfo=UTC),
    )
    view_model = MainViewModel(chart_service=service)
    controller = UiController(context=MagicMock())
    view = MarketView(view_model=view_model, controller=controller)
    view.show()
    qapp.processEvents()

    assert view._diag_tick_count.text() == "1"  # noqa: SLF001
    assert view._diag_candle_count.text() == "1"  # noqa: SLF001
    assert view._diag_last_symbol.text() == DEFAULT_SYMBOL  # noqa: SLF001
    assert view._diag_last_price.text() == "70100"  # noqa: SLF001
    assert "2024-06-20" in view._diag_last_time.text()  # noqa: SLF001
