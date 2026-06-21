"""Order repository tests."""

from __future__ import annotations

import pytest
from tests.fixtures.database_fixtures import build_test_database_manager

from app.domain.order.order import Order

pytestmark = pytest.mark.unit


def test_order_repository_save_and_get(tmp_path) -> None:
    manager = build_test_database_manager(tmp_path)
    repository = manager.build_order_repository()
    order = Order(
        order_number="ORD-001",
        order_branch="001",
        symbol_code="005930",
        side="buy",
        quantity="1",
        price="70000",
        status="submitted",
    )
    repository.save(order)
    loaded = repository.get("ORD-001")
    assert loaded is not None
    assert loaded.symbol_code == "005930"


def test_order_repository_update_status(tmp_path) -> None:
    manager = build_test_database_manager(tmp_path)
    repository = manager.build_order_repository()
    order = Order(
        order_number="ORD-002",
        order_branch="001",
        symbol_code="005930",
        side="sell",
        quantity="1",
        price="71000",
    )
    repository.save(order)
    assert repository.update_status("ORD-002", "filled") is True
    loaded = repository.get("ORD-002")
    assert loaded is not None
    assert loaded.status == "filled"
