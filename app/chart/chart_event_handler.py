"""EventBus handlers for chart candle updates."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.events.base_event import BaseEvent
from app.events.event_bus_service import EventBusService
from app.events.event_types import EventType

if TYPE_CHECKING:
    from app.service.chart.chart_service import ChartService


class ChartEventHandler:
    """Routes MarketDataEvent payloads to ChartService."""

    def __init__(self, *, chart_service: ChartService) -> None:
        self._chart_service = chart_service
        self._subscription_ids: list[str] = []

    @property
    def subscription_ids(self) -> tuple[str, ...]:
        """Return active EventBus subscription IDs."""
        return tuple(self._subscription_ids)

    def handle_market_data(self, event: BaseEvent) -> None:
        """Handle MarketDataEvent."""
        self._chart_service.on_market_tick(event.payload)

    def register(self, event_bus: EventBusService) -> tuple[str, ...]:
        """Subscribe chart handlers to EventBus."""
        self._subscription_ids = [
            event_bus.subscribe(EventType.MARKET_DATA, self.handle_market_data),
        ]
        return tuple(self._subscription_ids)

    def unregister(self, event_bus: EventBusService) -> None:
        """Unsubscribe all chart handlers."""
        for subscription_id in self._subscription_ids:
            event_bus.unsubscribe(subscription_id)
        self._subscription_ids.clear()
