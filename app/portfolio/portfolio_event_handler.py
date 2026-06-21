"""EventBus handlers for portfolio updates."""

from __future__ import annotations

from app.events.base_event import BaseEvent
from app.events.event_bus_service import EventBusService
from app.events.event_types import EventType
from app.portfolio.portfolio_engine import PortfolioEngine


class PortfolioEventHandler:
    """Routes EventBus events to PortfolioEngine."""

    def __init__(self, *, engine: PortfolioEngine) -> None:
        self._engine = engine
        self._subscription_ids: list[str] = []

    @property
    def subscription_ids(self) -> tuple[str, ...]:
        """Return active EventBus subscription IDs."""
        return tuple(self._subscription_ids)

    def handle_account(self, event: BaseEvent) -> None:
        """Handle AccountEvent."""
        self._engine.apply_account(event.payload)

    def handle_execution(self, event: BaseEvent) -> None:
        """Handle ExecutionEvent."""
        self._engine.apply_execution(event.payload)

    def handle_market_data(self, event: BaseEvent) -> None:
        """Handle MarketDataEvent."""
        self._engine.apply_market_data(event.payload)

    def register(self, event_bus: EventBusService) -> tuple[str, ...]:
        """Subscribe portfolio handlers to EventBus."""
        self._subscription_ids = [
            event_bus.subscribe(EventType.ACCOUNT, self.handle_account),
            event_bus.subscribe(EventType.EXECUTION, self.handle_execution),
            event_bus.subscribe(EventType.MARKET_DATA, self.handle_market_data),
        ]
        return tuple(self._subscription_ids)

    def unregister(self, event_bus: EventBusService) -> None:
        """Unsubscribe all portfolio handlers."""
        for subscription_id in self._subscription_ids:
            event_bus.unsubscribe(subscription_id)
        self._subscription_ids.clear()
