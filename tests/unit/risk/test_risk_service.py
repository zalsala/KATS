"""RiskService tests."""

from __future__ import annotations

from decimal import Decimal

import pytest
from tests.fixtures.event_fixtures import build_test_event_bus_service
from tests.fixtures.portfolio_fixtures import build_test_portfolio_service
from tests.fixtures.risk_fixtures import (
    build_test_buy_signal,
    build_test_risk_policy,
    build_test_risk_service,
)

from app.service.risk.risk_service import build_risk_service

pytestmark = pytest.mark.unit


def test_validate_signal_approved() -> None:
    service = build_test_risk_service(policy=build_test_risk_policy())
    result = service.validate_signal(
        build_test_buy_signal(price=Decimal("10000"), quantity=Decimal("1"))
    )

    assert result.approved is True
    assert result.status == "APPROVED"


def test_start_registers_event_handlers() -> None:
    event_bus = build_test_event_bus_service()
    portfolio_service = build_test_portfolio_service()
    service = build_risk_service(portfolio_service=portfolio_service, event_bus=event_bus)
    service.start(event_bus)

    assert len(service.event_handler.subscription_ids) == 2
