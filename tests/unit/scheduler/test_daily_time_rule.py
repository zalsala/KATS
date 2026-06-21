"""DailyTimeRule tests."""

from __future__ import annotations

import pytest
from tests.fixtures.scheduler_fixtures import utc_at

from app.scheduler.rules import DailyTimeRule

pytestmark = pytest.mark.unit


def test_daily_time_rule_due_after_scheduled_time() -> None:
    rule = DailyTimeRule(hour=9, minute=0, timezone="UTC")
    now = utc_at(2024, 1, 2, 9, 30)
    assert rule.is_due(now, None) is True


def test_daily_time_rule_not_due_before_scheduled_time() -> None:
    rule = DailyTimeRule(hour=9, minute=0, timezone="UTC")
    now = utc_at(2024, 1, 2, 8, 59)
    assert rule.is_due(now, None) is False


def test_daily_time_rule_not_due_twice_same_day() -> None:
    rule = DailyTimeRule(hour=9, minute=0, timezone="UTC")
    now = utc_at(2024, 1, 2, 10, 0)
    last_run = utc_at(2024, 1, 2, 9, 5)
    assert rule.is_due(now, last_run) is False
