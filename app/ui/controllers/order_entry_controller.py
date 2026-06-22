"""Order entry controller."""

from __future__ import annotations

import logging

from app.dto.order.order_entry_request import OrderEntryRequest
from app.service.order.order_service import OrderValidationError
from app.service.trading.trading_service import TradingNotAllowedError, TradingService
from app.ui.viewmodels.main_view_model import MainViewModel

logger = logging.getLogger(__name__)


class OrderEntryController:
    """Validate and submit order entry requests from the market view."""

    def __init__(
        self,
        *,
        trading_service: TradingService,
        view_model: MainViewModel,
    ) -> None:
        self._trading_service = trading_service
        self._view_model = view_model

    def initialize(self) -> None:
        """Initialize trading availability and sync the active symbol."""
        self.refresh_trading_status()
        symbol = (
            self._view_model.watchlist.selected_symbol
            or self._view_model.chart.symbol_code
            or self._view_model.market.symbol_input
        )
        if symbol:
            self.sync_symbol(symbol)

    def refresh_trading_status(self) -> None:
        """Refresh whether order submission is currently allowed."""
        enabled = self._trading_service.is_trading_available()
        message = self._trading_service.trading_status_message()
        self._view_model.order_entry.set_trading_status(enabled=enabled, message=message)

    def sync_symbol(self, symbol_code: str) -> None:
        """Sync the order form symbol from watchlist or chart selection."""
        self._view_model.order_entry.sync_symbol(symbol_code)

    def validate(self, request: OrderEntryRequest | None = None) -> list[str]:
        """Validate the current or provided order entry request."""
        entry = request or self._view_model.order_entry.build_request()
        return self._trading_service.validate(entry)

    def submit(self) -> bool:
        """Validate and submit the current order entry form."""
        entry_vm = self._view_model.order_entry
        entry_vm.clear_error_message()
        request = entry_vm.build_request()
        errors = self.validate(request)
        if errors:
            entry_vm.set_error_message(errors[0])
            entry_vm.set_result(success=False, message=errors[0])
            return False

        try:
            result = self._trading_service.place_order(request)
        except TradingNotAllowedError as exc:
            entry_vm.set_error_message(exc.message)
            entry_vm.set_result(success=False, message=exc.message)
            return False
        except OrderValidationError as exc:
            entry_vm.set_error_message(str(exc))
            entry_vm.set_result(success=False, message=str(exc))
            return False
        except Exception:
            logger.exception("Order submission failed for symbol=%s", request.symbol_code)
            message = "Order submission failed"
            entry_vm.set_error_message(message)
            entry_vm.set_result(success=False, message=message)
            return False

        message = result.msg1 or result.order_number or "Order submitted"
        entry_vm.set_result(success=result.success, message=message)
        if result.success:
            self._view_model.set_status_message(f"Order submitted: {message}")
        else:
            entry_vm.set_error_message(message)
        return result.success

    def reset(self) -> None:
        """Reset the order entry form."""
        self._view_model.order_entry.reset_form()
