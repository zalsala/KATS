"""Emergency stop risk tests."""

from __future__ import annotations

import pytest
from tests.fixtures.risk_fixtures import build_test_buy_signal, build_test_risk_service

pytestmark = pytest.mark.unit


def test_emergency_stop_rejects_all_signals() -> None:
    service = build_test_risk_service()
    service.set_emergency_stop(True)

    result = service.validate_signal(build_test_buy_signal())

    assert result.approved is False
    assert any(item.rule_code == "emergency_stop" for item in result.violations)
