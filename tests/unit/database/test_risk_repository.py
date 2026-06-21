"""Risk policy repository tests."""

from __future__ import annotations

from decimal import Decimal

import pytest
from tests.fixtures.database_fixtures import build_test_database_manager

from app.domain.risk.risk_policy import RiskPolicy

pytestmark = pytest.mark.unit


def test_risk_policy_repository_save_and_get(tmp_path) -> None:
    manager = build_test_database_manager(tmp_path)
    repository = manager.build_risk_policy_repository()
    policy = RiskPolicy(
        max_order_amount=Decimal("1000000"),
        max_order_quantity=Decimal("100"),
        max_position_count=5,
        max_symbol_weight=Decimal("0.3"),
        daily_loss_limit=Decimal("0.05"),
        duplicate_order_block=True,
        emergency_stop=False,
    )
    repository.save(policy, policy_name="default")
    loaded = repository.get("default")
    assert loaded is not None
    assert loaded.max_position_count == 5
