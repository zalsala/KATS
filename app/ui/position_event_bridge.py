"""EventBus bridge for position panel updates."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from app.events.base_event import BaseEvent
from app.events.event_bus_service import EventBusService
from app.events.event_types import EventType
from app.ui.controllers.position_controller import PositionController


class PositionEventBridge:
    """Updates position valuation when realtime market data arrives."""

    def __init__(self, *, position_controller: PositionController) -> None:
        self._position_controller = position_controller
        self._subscription_ids: list[str] = []

    def register(self, event_bus: EventBusService) -> tuple[str, ...]:
        """Subscribe position refresh handlers."""
        self._subscription_ids = [
            event_bus.subscribe(EventType.MARKET_DATA, self._handle_market_data),
        ]
        return tuple(self._subscription_ids)

    def unregister(self, event_bus: EventBusService) -> None:
        """Unsubscribe position refresh handlers."""
        for subscription_id in self._subscription_ids:
            event_bus.unsubscribe(subscription_id)
        self._subscription_ids.clear()

    def _handle_market_data(self, event: BaseEvent) -> None:
        symbol = str(event.payload.get("symbol_code", event.payload.get("symbol", ""))).strip()
        price_raw = event.payload.get("price", event.payload.get("current_price"))
        if not symbol or price_raw is None:
            return
        try:
            price = Decimal(str(price_raw))
        except (InvalidOperation, ValueError):
            return
        self._position_controller.on_market_tick(symbol, price)
