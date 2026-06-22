"""Watchlist controller."""

from __future__ import annotations

import logging
from decimal import Decimal

from app.service.watchlist.watchlist_service import WatchlistService, WatchlistValidationError
from app.ui.controllers.ui_controller import UiController
from app.ui.models.watchlist_item import WatchlistItem
from app.ui.viewmodels.main_view_model import MainViewModel

logger = logging.getLogger(__name__)


class WatchlistController:
    """Coordinate watchlist actions, subscriptions, and chart updates."""

    def __init__(
        self,
        *,
        controller: UiController,
        watchlist_service: WatchlistService,
        view_model: MainViewModel,
    ) -> None:
        self._controller = controller
        self._watchlist_service = watchlist_service
        self._view_model = view_model
        self._active_subscription: str | None = None

    @property
    def active_subscription(self) -> str | None:
        """Return the symbol currently subscribed for chart realtime data."""
        return self._active_subscription

    def initialize(self) -> None:
        """Load persisted watchlist state and restore selection."""
        items = list(self._watchlist_service.load_items())
        selected_symbol = self._watchlist_service.load_selected_symbol()

        if not items:
            items = [WatchlistItem(symbol_code="005930", name="005930")]

        if selected_symbol is None or not any(
            item.symbol_code == selected_symbol for item in items
        ):
            selected_symbol = items[0].symbol_code

        self._view_model.watchlist.set_items(items)
        self.select_symbol(selected_symbol, persist=False)
        self._persist()

    def shutdown(self) -> None:
        """Persist watchlist state on application exit."""
        self._persist()

    def add_symbol(self, symbol_code: str) -> bool:
        """Add a symbol to the watchlist after validation."""
        self._view_model.watchlist.clear_error_message()
        try:
            normalized = self._watchlist_service.validate_symbol_code(symbol_code)
        except WatchlistValidationError as exc:
            self._view_model.watchlist.set_error_message(exc.message)
            return False

        if any(item.symbol_code == normalized for item in self._view_model.watchlist.items):
            self._view_model.watchlist.set_error_message("Symbol is already in the watchlist")
            return False

        try:
            item = self._watchlist_service.resolve_symbol(normalized)
        except WatchlistValidationError as exc:
            self._view_model.watchlist.set_error_message(exc.message)
            return False

        items = [*self._view_model.watchlist.items, item]
        self._view_model.watchlist.set_items(items)
        self.select_symbol(item.symbol_code)
        self._view_model.set_status_message(f"Added to watchlist: {item.symbol_code}")
        return True

    def remove_selected(self) -> bool:
        """Remove the selected watchlist symbol."""
        self._view_model.watchlist.clear_error_message()
        selected = self._view_model.watchlist.selected_symbol
        if selected is None:
            self._view_model.watchlist.set_error_message("Select a symbol to remove")
            return False

        remaining = [
            item for item in self._view_model.watchlist.items if item.symbol_code != selected
        ]
        if not remaining:
            self._release_active_subscription()
            self._view_model.watchlist.set_items([])
            self._view_model.watchlist.set_selected_symbol(None)
            self._view_model.chart.candles = []
            self._view_model.chart.indicator_series = {}
            self._view_model.chart.notify("candles")
            self._view_model.chart.notify("indicators")
            self._persist()
            self._view_model.set_status_message("Watchlist is empty")
            return True

        self._release_active_subscription()
        self._view_model.watchlist.set_items(remaining)
        next_symbol = remaining[0].symbol_code
        self.select_symbol(next_symbol)
        self._view_model.set_status_message(f"Removed from watchlist: {selected}")
        return True

    def select_symbol(self, symbol_code: str, *, persist: bool = True) -> None:
        """Switch chart and realtime subscription to a watchlist symbol."""
        if not any(item.symbol_code == symbol_code for item in self._view_model.watchlist.items):
            return

        self._switch_subscription(symbol_code)
        self._view_model.watchlist.set_selected_symbol(symbol_code)
        self._view_model.market.set_symbol_input(symbol_code)
        self._view_model.chart.set_symbol(symbol_code)
        if persist:
            self._persist()

    def handle_market_tick(
        self,
        *,
        symbol_code: str,
        price: Decimal,
    ) -> None:
        """Apply a realtime quote update to the watchlist row."""
        if symbol_code != self._active_subscription:
            return

        item = self._view_model.watchlist.get_item(symbol_code)
        if item is None:
            return

        updated = self._watchlist_service.apply_live_price(item, price)
        self._view_model.watchlist.update_row_price(
            symbol_code=symbol_code,
            price=updated.last_price or price,
            change_amount=updated.change_amount,
            change_percent=updated.change_percent,
            is_live=True,
        )
        self._view_model.market.update_price(
            symbol_code=symbol_code,
            price=price,
        )

    def _switch_subscription(self, symbol_code: str) -> None:
        if self._active_subscription == symbol_code:
            return

        self._release_active_subscription()
        try:
            self._controller.subscribe_realtime_price(symbol_code)
            self._view_model.market.add_subscription(symbol_code)
            self._active_subscription = symbol_code
        except Exception:
            logger.exception("Failed to subscribe watchlist symbol %s", symbol_code)
            self._view_model.watchlist.set_error_message(
                f"Failed to subscribe realtime data for {symbol_code}",
            )

    def _release_active_subscription(self) -> None:
        if self._active_subscription is None:
            return
        try:
            self._controller.unsubscribe_realtime_price(self._active_subscription)
        except Exception:
            logger.exception(
                "Failed to unsubscribe watchlist symbol %s",
                self._active_subscription,
            )
        self._view_model.market.remove_subscription(self._active_subscription)
        self._active_subscription = None

    def _persist(self) -> None:
        self._watchlist_service.save_state(
            items=tuple(self._view_model.watchlist.items),
            selected_symbol=self._view_model.watchlist.selected_symbol,
        )
