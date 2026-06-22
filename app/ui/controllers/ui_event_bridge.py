"""EventBus bridge for UI view model updates."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from app.events.base_event import BaseEvent
from app.events.event_bus_service import EventBusService
from app.events.event_types import EventType
from app.ui.controllers.ui_controller import UiController
from app.ui.controllers.watchlist_controller import WatchlistController
from app.ui.viewmodels.main_view_model import MainViewModel


class UiEventBridge:
    """Subscribes to EventBus events and refreshes view models."""

    def __init__(
        self,
        *,
        controller: UiController,
        view_model: MainViewModel,
        watchlist_controller: WatchlistController | None = None,
    ) -> None:
        self._controller = controller
        self._view_model = view_model
        self._watchlist_controller = watchlist_controller
        self._subscription_ids: list[str] = []

    def register(self, event_bus: EventBusService) -> tuple[str, ...]:
        """Subscribe UI refresh handlers."""
        self._subscription_ids = [
            event_bus.subscribe(EventType.PORTFOLIO, self._handle_portfolio),
            event_bus.subscribe(EventType.MARKET_DATA, self._handle_market_data),
            event_bus.subscribe(EventType.STRATEGY, self._handle_strategy),
            event_bus.subscribe(EventType.RISK, self._handle_risk),
            event_bus.subscribe(EventType.SYSTEM, self._handle_system),
        ]
        return tuple(self._subscription_ids)

    def unregister(self, event_bus: EventBusService) -> None:
        """Unsubscribe UI handlers."""
        for subscription_id in self._subscription_ids:
            event_bus.unsubscribe(subscription_id)
        self._subscription_ids.clear()

    def refresh_all(self) -> None:
        """Refresh all view models from services."""
        summary, positions = self._controller.refresh_portfolio_state()
        self._view_model.dashboard.update_summary(summary)
        self._view_model.dashboard.update_connection_status(
            self._controller.get_connection_status()
        )
        self._view_model.dashboard.update_emergency_stop(
            self._controller.is_emergency_stop_active()
        )
        self._view_model.dashboard.update_running_strategy_count(
            self._controller.count_running_strategies()
        )
        self._view_model.portfolio.update(summary=summary, positions=positions)
        self._view_model.strategy.update_strategies(self._controller.list_strategy_rows())
        env, account_type, version = self._controller.load_settings()
        self._view_model.settings.update(
            environment=env,
            account_type=account_type,
            application_version=version,
        )

    def _handle_portfolio(self, event: BaseEvent) -> None:
        self._append_log("INFO", f"Portfolio updated: {event.payload.get('reason', '')}")
        self.refresh_all()

    def _handle_market_data(self, event: BaseEvent) -> None:
        symbol = str(event.payload.get("symbol_code", event.payload.get("symbol", "")))
        price_raw = event.payload.get("price", event.payload.get("current_price", "0"))
        self._view_model.market.update_price(
            symbol_code=symbol,
            price=Decimal(str(price_raw)),
            updated_at=datetime.now(UTC).isoformat(),
        )
        if self._watchlist_controller is not None and symbol:
            self._watchlist_controller.handle_market_tick(
                symbol_code=symbol,
                price=Decimal(str(price_raw)),
            )

    def _handle_strategy(self, event: BaseEvent) -> None:
        signal_type = event.payload.get("signal_type", "")
        self._append_log("INFO", f"Strategy event: {signal_type}")
        self._view_model.strategy.update_strategies(self._controller.list_strategy_rows())
        self._view_model.dashboard.update_running_strategy_count(
            self._controller.count_running_strategies()
        )

    def _handle_risk(self, event: BaseEvent) -> None:
        status = event.payload.get("status", "")
        self._append_log("WARN" if status == "REJECTED" else "INFO", f"Risk {status}")
        self._view_model.dashboard.update_emergency_stop(
            self._controller.is_emergency_stop_active()
        )

    def _handle_system(self, event: BaseEvent) -> None:
        if event.event_name == "notification.created":
            payload = event.payload
            level = str(payload.get("level", "INFO"))
            message = str(payload.get("body", payload.get("title", "Notification")))
            self._append_log(level, message)
            return
        self._view_model.dashboard.update_connection_status(
            self._controller.get_connection_status()
        )
        self._append_log("INFO", event.payload.get("message", "System event"))

    def _append_log(self, level: str, message: str) -> None:
        self._view_model.log.append(self._controller.build_log_entry(level=level, message=message))
