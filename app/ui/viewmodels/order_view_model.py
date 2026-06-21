"""Order view model."""

from __future__ import annotations

from app.ui.models.display_models import OrderFormData
from app.ui.viewmodels.base import ViewModelBase


class OrderViewModel(ViewModelBase):
    """State and validation for the order view."""

    def __init__(self) -> None:
        super().__init__()
        self.last_message: str = ""
        self.last_success: bool = False

    def validate_form(self, form: OrderFormData) -> list[str]:
        """Validate order form input (UI-level only)."""
        errors: list[str] = []
        if not form.symbol_code.strip():
            errors.append("symbol_code_required")
        if not form.quantity.strip().isdigit() or int(form.quantity) <= 0:
            errors.append("quantity_must_be_positive")
        if not form.price.strip().isdigit() or int(form.price) <= 0:
            errors.append("price_must_be_positive")
        if form.side not in {"buy", "sell"}:
            errors.append("invalid_side")
        return errors

    def set_result(self, *, success: bool, message: str) -> None:
        self.last_success = success
        self.last_message = message
        self.notify("result")
