"""ViewModel unit tests."""

from __future__ import annotations

import pytest

from app.ui.models.display_models import OrderFormData
from app.ui.viewmodels.main_view_model import MainViewModel
from app.ui.viewmodels.order_view_model import OrderViewModel

pytestmark = pytest.mark.unit


def test_main_view_model_active_view() -> None:
    vm = MainViewModel()
    changes: list[str] = []
    vm.add_listener(lambda field: changes.append(field))
    vm.set_active_view("portfolio")
    assert vm.active_view == "portfolio"
    assert changes == ["active_view"]


def test_order_view_model_validation_success() -> None:
    vm = OrderViewModel()
    errors = vm.validate_form(
        OrderFormData(symbol_code="005930", quantity="1", price="70000", side="buy")
    )
    assert errors == []


def test_order_view_model_validation_failure() -> None:
    vm = OrderViewModel()
    errors = vm.validate_form(OrderFormData(symbol_code="", quantity="0", price="0", side="buy"))
    assert "symbol_code_required" in errors
    assert "quantity_must_be_positive" in errors
