"""EventBus handlers for strategy execution."""

from __future__ import annotations

from app.events.base_event import BaseEvent
from app.events.event_bus_service import EventBusService
from app.events.event_types import EventType
from app.strategy.strategy_engine import StrategyEngine


class StrategyEventHandler:
    """Routes EventBus events to StrategyEngine."""

    def __init__(self, *, engine: StrategyEngine) -> None:
        self._engine = engine
        self._subscription_ids: list[str] = []

    @property
    def subscription_ids(self) -> tuple[str, ...]:
        """Return active EventBus subscription IDs."""
        return tuple(self._subscription_ids)

    def handle_market_data(self, event: BaseEvent) -> None:
        """Handle MarketDataEvent."""
        self._engine.handle_market_data(event.payload)

    def handle_execution(self, event: BaseEvent) -> None:
        """Handle ExecutionEvent."""
        self._engine.handle_execution(event.payload)

    def handle_portfolio(self, event: BaseEvent) -> None:
        """Handle PortfolioEvent."""
        self._engine.handle_portfolio_changed(event.payload)

    def register(self, event_bus: EventBusService) -> tuple[str, ...]:
        """Subscribe strategy handlers to EventBus."""
        self._subscription_ids = [
            event_bus.subscribe(EventType.MARKET_DATA, self.handle_market_data),
            event_bus.subscribe(EventType.EXECUTION, self.handle_execution),
            event_bus.subscribe(EventType.PORTFOLIO, self.handle_portfolio),
        ]
        return tuple(self._subscription_ids)

    def unregister(self, event_bus: EventBusService) -> None:
        """Unsubscribe all strategy handlers."""
        for subscription_id in self._subscription_ids:
            event_bus.unsubscribe(subscription_id)
        self._subscription_ids.clear()
