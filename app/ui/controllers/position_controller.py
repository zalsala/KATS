"""Position panel controller."""

from __future__ import annotations

import logging
from decimal import Decimal

from app.service.trading.trading_service import TradingNotAllowedError, TradingService
from app.ui.viewmodels.main_view_model import MainViewModel

logger = logging.getLogger(__name__)


class PositionController:
    """Load and refresh domestic stock holdings for the market view."""

    def __init__(
        self,
        *,
        trading_service: TradingService,
        view_model: MainViewModel,
    ) -> None:
        self._trading_service = trading_service
        self._view_model = view_model

    def initialize(self) -> None:
        """Initialize lookup availability, selection, and initial holdings."""
        self.refresh_lookup_status()
        symbol = (
            self._view_model.watchlist.selected_symbol
            or self._view_model.chart.symbol_code
            or self._view_model.market.symbol_input
        )
        if symbol:
            self.sync_selected_symbol(symbol)
        self.refresh()

    def refresh_lookup_status(self) -> None:
        """Refresh whether position lookup is currently allowed."""
        enabled = self._trading_service.is_position_lookup_available()
        message = self._trading_service.position_lookup_status_message()
        self._view_model.position.set_lookup_status(enabled=enabled, message=message)

    def sync_selected_symbol(self, symbol_code: str) -> None:
        """Sync the highlighted position row from watchlist or chart selection."""
        self._view_model.position.set_selected_symbol(symbol_code)

    def refresh(self) -> bool:
        """Refresh holdings from the trading service."""
        position_vm = self._view_model.position
        position_vm.clear_error_message()
        if not self._trading_service.is_position_lookup_available():
            position_vm.set_positions([])
            message = self._trading_service.position_lookup_status_message()
            position_vm.set_error_message(message)
            return False

        position_vm.set_loading(True)
        try:
            positions = self._trading_service.get_positions()
        except TradingNotAllowedError as exc:
            position_vm.set_positions([])
            position_vm.set_error_message(exc.message)
            return False
        except Exception:
            logger.exception("Position refresh failed")
            position_vm.set_positions([])
            position_vm.set_error_message("Failed to load positions")
            return False
        finally:
            position_vm.set_loading(False)

        position_vm.set_positions(positions)
        return True

    def on_market_tick(self, symbol_code: str, price: Decimal) -> None:
        """Update held position valuation when a realtime tick arrives."""
        if not symbol_code:
            return
        self._view_model.position.update_market_price(symbol_code, price)
