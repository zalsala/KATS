"""Chart event handler tests."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.chart.chart_event_handler import ChartEventHandler
from app.chart.in_memory_candle_store import InMemoryCandleStore
from app.events.domain_events import MarketDataEvent
from app.events.event_bus_service import EventBusService
from app.events.in_memory_event_bus import InMemoryEventBus
from app.service.chart.chart_service import ChartService

pytestmark = pytest.mark.unit


def test_chart_event_handler_registers_and_routes_market_data() -> None:
    event_bus = EventBusService(event_bus=InMemoryEventBus())
    service = ChartService(store=InMemoryCandleStore())
    handler = ChartEventHandler(chart_service=service)
    handler.register(event_bus)

    event_bus.publish(
        MarketDataEvent(
            source="websocket",
            payload={
                "symbol_code": "005930",
                "price": "70200",
                "volume": "2",
                "timestamp": datetime(2024, 6, 20, 12, 1, 5, tzinfo=UTC).isoformat(),
            },
        )
    )

    candle = service.get_candles("005930")[0]
    assert candle.close == Decimal("70200")
    assert len(handler.subscription_ids) == 1

    handler.unregister(event_bus)
    assert handler.subscription_ids == ()
