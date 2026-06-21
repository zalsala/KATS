"""EventBus handlers for risk validation."""

from __future__ import annotations

from app.events.base_event import BaseEvent
from app.events.event_bus_service import EventBusService
from app.events.event_types import EventType
from app.risk.risk_engine import RiskEngine


class RiskEventHandler:
    """Routes EventBus events to RiskEngine."""

    def __init__(self, *, engine: RiskEngine) -> None:
        self._engine = engine
        self._subscription_ids: list[str] = []

    @property
    def subscription_ids(self) -> tuple[str, ...]:
        """Return active EventBus subscription IDs."""
        return tuple(self._subscription_ids)

    def handle_strategy(self, event: BaseEvent) -> None:
        """Handle StrategyEvent and validate extracted signal."""
        self._engine.handle_strategy_signal(event.payload)

    def handle_execution(self, event: BaseEvent) -> None:
        """Handle ExecutionEvent to clear pending orders."""
        self._engine.handle_execution(event.payload)

    def register(self, event_bus: EventBusService) -> tuple[str, ...]:
        """Subscribe risk handlers to EventBus."""
        self._subscription_ids = [
            event_bus.subscribe(EventType.STRATEGY, self.handle_strategy),
            event_bus.subscribe(EventType.EXECUTION, self.handle_execution),
        ]
        return tuple(self._subscription_ids)

    def unregister(self, event_bus: EventBusService) -> None:
        """Unsubscribe all risk handlers."""
        for subscription_id in self._subscription_ids:
            event_bus.unsubscribe(subscription_id)
        self._subscription_ids.clear()
