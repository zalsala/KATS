"""MarketTimeRule tests."""

from __future__ import annotations

import pytest
from tests.fixtures.scheduler_fixtures import utc_at

from app.scheduler.rules import MarketTimeRule

pytestmark = pytest.mark.unit


def test_market_open_rule_due_on_weekday() -> None:
    rule = MarketTimeRule(market_event="open", timezone="UTC")
    now = utc_at(2024, 1, 3, 9, 5)  # Wednesday
    assert rule.is_due(now, None) is True


def test_market_open_rule_not_due_on_weekend() -> None:
    rule = MarketTimeRule(market_event="open", timezone="UTC")
    now = utc_at(2024, 1, 6, 9, 5)  # Saturday
    assert rule.is_due(now, None) is False


def test_market_close_rule_not_due_twice_same_session() -> None:
    rule = MarketTimeRule(market_event="close", timezone="UTC")
    now = utc_at(2024, 1, 3, 16, 0)
    last_run = utc_at(2024, 1, 3, 15, 31)
    assert rule.is_due(now, last_run) is False
