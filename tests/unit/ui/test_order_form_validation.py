"""Order form validation tests."""

from __future__ import annotations

import pytest

from app.ui.models.display_models import OrderFormData
from app.ui.viewmodels.order_view_model import OrderViewModel

pytestmark = pytest.mark.unit


def test_invalid_side_rejected() -> None:
    vm = OrderViewModel()
    errors = vm.validate_form(
        OrderFormData(symbol_code="005930", quantity="1", price="100", side="hold")
    )
    assert "invalid_side" in errors
