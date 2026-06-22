"""Account summary panel controller."""

from __future__ import annotations

import logging
from decimal import Decimal

from app.service.trading.trading_service import TradingNotAllowedError, TradingService
from app.ui.viewmodels.main_view_model import MainViewModel

logger = logging.getLogger(__name__)


class AccountSummaryController:
    """Load and refresh domestic stock account summary for the market view."""

    def __init__(
        self,
        *,
        trading_service: TradingService,
        view_model: MainViewModel,
    ) -> None:
        self._trading_service = trading_service
        self._view_model = view_model

    def initialize(self) -> None:
        """Initialize lookup availability and load the initial summary."""
        self.refresh_lookup_status()
        self.refresh()

    def refresh_lookup_status(self) -> None:
        """Refresh whether account summary lookup is currently allowed."""
        enabled = self._trading_service.is_account_summary_available()
        message = self._trading_service.account_summary_status_message()
        self._view_model.account_summary.set_lookup_status(enabled=enabled, message=message)

    def refresh(self) -> bool:
        """Refresh account summary from the trading service."""
        summary_vm = self._view_model.account_summary
        summary_vm.clear_error_message()
        if not self._trading_service.is_account_summary_available():
            summary_vm.set_summary(None)
            message = self._trading_service.account_summary_status_message()
            summary_vm.set_error_message(message)
            return False

        summary_vm.set_loading(True)
        try:
            summary = self._trading_service.get_account_summary()
        except TradingNotAllowedError as exc:
            summary_vm.set_summary(None)
            summary_vm.set_error_message(exc.message)
            return False
        except Exception:
            logger.exception("Account summary refresh failed")
            summary_vm.set_summary(None)
            summary_vm.set_error_message("Failed to load account summary")
            return False
        finally:
            summary_vm.set_loading(False)

        summary_vm.set_summary(summary)
        return True

    def on_market_tick(self, symbol_code: str, price: Decimal) -> None:
        """Update account valuation when a held symbol tick arrives."""
        if not symbol_code:
            return
        positions = self._view_model.position.positions
        if not any(position.symbol_code == symbol_code for position in positions):
            return
        self._view_model.position.update_market_price(symbol_code, price)
        self._view_model.account_summary.recalculate_from_positions(
            self._view_model.position.positions
        )
