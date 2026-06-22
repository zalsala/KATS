"""Position panel view model."""

from __future__ import annotations

from decimal import Decimal

from app.domain.position.position_item import PositionItem
from app.ui.viewmodels.base import ViewModelBase


class PositionViewModel(ViewModelBase):
    """State for the embedded market position panel."""

    def __init__(self) -> None:
        super().__init__()
        self.positions: list[PositionItem] = []
        self.selected_symbol: str = ""
        self.loading: bool = False
        self.lookup_enabled: bool = False
        self.lookup_status: str = ""
        self.error_message: str = ""

    def set_lookup_status(self, *, enabled: bool, message: str) -> None:
        """Update whether position lookup is currently allowed."""
        self.lookup_enabled = enabled
        self.lookup_status = message
        self.notify("lookup_status")

    def set_loading(self, loading: bool) -> None:
        self.loading = loading
        self.notify("loading")

    def set_positions(self, positions: list[PositionItem]) -> None:
        self.positions = list(positions)
        self.notify("positions")

    def set_selected_symbol(self, symbol_code: str) -> None:
        normalized = symbol_code.strip()
        if normalized == self.selected_symbol:
            return
        self.selected_symbol = normalized
        self.notify("selected_symbol")

    def set_error_message(self, message: str) -> None:
        self.error_message = message
        self.notify("error_message")

    def clear_error_message(self) -> None:
        if not self.error_message:
            return
        self.error_message = ""
        self.notify("error_message")

    def update_market_price(self, symbol_code: str, current_price: Decimal) -> bool:
        """Update valuation for a held symbol when a market tick arrives."""
        normalized = symbol_code.strip()
        updated = False
        new_positions: list[PositionItem] = []
        for position in self.positions:
            if position.symbol_code == normalized:
                new_positions.append(position.with_current_price(current_price))
                updated = True
            else:
                new_positions.append(position)
        if not updated:
            return False
        self.positions = new_positions
        self.notify(f"row:{normalized}")
        return True
