"""EventBus bridge for chart view model refresh."""

from __future__ import annotations

from app.events.base_event import BaseEvent
from app.events.event_bus_service import EventBusService
from app.events.event_types import EventType
from app.ui.viewmodels.chart_view_model import ChartViewModel


class ChartEventBridge:
    """Refreshes ChartViewModel when realtime market data arrives."""

    def __init__(self, *, chart_view_model: ChartViewModel) -> None:
        self._chart_view_model = chart_view_model
        self._subscription_ids: list[str] = []

    def register(self, event_bus: EventBusService) -> tuple[str, ...]:
        """Subscribe chart refresh handlers."""
        self._subscription_ids = [
            event_bus.subscribe(EventType.MARKET_DATA, self._handle_market_data),
        ]
        return tuple(self._subscription_ids)

    def unregister(self, event_bus: EventBusService) -> None:
        """Unsubscribe chart refresh handlers."""
        for subscription_id in self._subscription_ids:
            event_bus.unsubscribe(subscription_id)
        self._subscription_ids.clear()

    def _handle_market_data(self, event: BaseEvent) -> None:
        symbol = str(event.payload.get("symbol_code", event.payload.get("symbol", ""))).strip()
        if symbol and symbol != self._chart_view_model.symbol_code:
            return
        self._chart_view_model.refresh()
