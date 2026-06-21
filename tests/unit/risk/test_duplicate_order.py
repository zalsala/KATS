"""Duplicate order risk tests."""

from __future__ import annotations

import pytest
from tests.fixtures.risk_fixtures import (
    build_test_buy_signal,
    build_test_risk_policy,
    build_test_risk_service,
)

pytestmark = pytest.mark.unit


def test_duplicate_order_blocked() -> None:
    policy = build_test_risk_policy()
    service = build_test_risk_service(policy=policy)
    signal = build_test_buy_signal()

    first = service.validate_signal(signal)
    second = service.validate_signal(signal)

    assert first.approved is True
    assert second.approved is False
    assert any(item.rule_code == "duplicate_order" for item in second.violations)
