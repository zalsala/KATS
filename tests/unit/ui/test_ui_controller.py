"""UI controller service binding tests."""

from __future__ import annotations

from decimal import Decimal

import pytest
from tests.fixtures.ui_fixtures import MockOrderService, build_test_ui_controller

from app.ui.models.display_models import OrderFormData

pytestmark = pytest.mark.unit


def test_controller_refresh_portfolio_state() -> None:
    controller = build_test_ui_controller()
    controller.context.portfolio_service.apply_account(
        {
            "account_no": "12345678",
            "total_deposit": "1000000",
            "orderable_cash": "900000",
            "holdings": [
                {
                    "symbol_code": "005930",
                    "stock_name": "Samsung",
                    "quantity": "1",
                    "average_price": "70000",
                    "current_price": "75000",
                }
            ],
        }
    )
    summary, positions = controller.refresh_portfolio_state()
    assert summary.total_asset > Decimal("0")
    assert len(positions) == 1


def test_controller_submit_order_uses_order_service() -> None:
    order_service = MockOrderService()
    controller = build_test_ui_controller(order_service=order_service)
    result = controller.submit_order(
        OrderFormData(symbol_code="005930", quantity="1", price="70000", side="buy")
    )
    assert result.success is True
    assert order_service.last_request is not None
