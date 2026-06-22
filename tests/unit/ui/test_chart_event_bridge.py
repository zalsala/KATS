"""Chart event bridge tests."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from PySide6.QtWidgets import QApplication

from app.chart.in_memory_candle_store import InMemoryCandleStore
from app.events.domain_events import MarketDataEvent
from app.events.event_bus_service import EventBusService
from app.events.in_memory_event_bus import InMemoryEventBus
from app.service.chart.chart_service import ChartService
from app.ui.chart_event_bridge import ChartEventBridge
from app.ui.viewmodels.chart_view_model import DEFAULT_SYMBOL, ChartViewModel
from app.ui.viewmodels.main_view_model import MainViewModel
from app.ui.views.market_view import MarketView

pytestmark = pytest.mark.unit


@pytest.fixture(scope="module")
def qapp():
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def _build_realtime_stack() -> (
    tuple[ChartService, EventBusService, ChartViewModel, ChartEventBridge]
):
    event_bus = EventBusService(event_bus=InMemoryEventBus())
    service = ChartService(store=InMemoryCandleStore(), event_bus=event_bus)
    service.start(event_bus)
    view_model = ChartViewModel(service, symbol_code=DEFAULT_SYMBOL)
    bridge = ChartEventBridge(chart_view_model=view_model)
    bridge.register(event_bus)
    return service, event_bus, view_model, bridge


def test_chart_event_bridge_refreshes_view_model() -> None:
    _service, event_bus, view_model, _bridge = _build_realtime_stack()
    changes: list[str] = []
    view_model.add_listener(lambda field: changes.append(field))

    event_bus.publish(
        MarketDataEvent(
            source="websocket",
            payload={
                "symbol_code": DEFAULT_SYMBOL,
                "price": "70300",
                "volume": "6",
                "timestamp": datetime(2024, 6, 20, 12, 1, 8, tzinfo=UTC).isoformat(),
            },
        )
    )

    assert changes == ["candles"]
    assert len(view_model.candles) == 1
    assert view_model.candles[0].close == Decimal("70300")


def test_chart_event_bridge_ignores_other_symbols() -> None:
    _service, event_bus, view_model, _bridge = _build_realtime_stack()

    event_bus.publish(
        MarketDataEvent(
            source="websocket",
            payload={
                "symbol_code": "000660",
                "price": "120000",
                "volume": "1",
                "timestamp": datetime(2024, 6, 20, 12, 1, 8, tzinfo=UTC).isoformat(),
            },
        )
    )

    assert view_model.candles == []


def test_market_view_updates_chart_on_realtime_event(qapp) -> None:
    event_bus = EventBusService(event_bus=InMemoryEventBus())
    service = ChartService(store=InMemoryCandleStore(), event_bus=event_bus)
    service.start(event_bus)
    view_model = MainViewModel(chart_service=service)
    bridge = ChartEventBridge(chart_view_model=view_model.chart)
    bridge.register(event_bus)
    view = MarketView(view_model=view_model)
    view.show()
    qapp.processEvents()

    assert view.chart_widget.is_empty is True

    event_bus.publish(
        MarketDataEvent(
            source="websocket",
            payload={
                "symbol_code": DEFAULT_SYMBOL,
                "price": "70400",
                "volume": "3",
                "timestamp": datetime(2024, 6, 20, 12, 1, 12, tzinfo=UTC).isoformat(),
            },
        )
    )
    qapp.processEvents()

    assert view.chart_widget.is_empty is False
    assert view.chart_widget.symbol == DEFAULT_SYMBOL
    view.chart_widget.repaint()
    qapp.processEvents()
