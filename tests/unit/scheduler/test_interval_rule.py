"""IntervalRule tests."""

from __future__ import annotations

from datetime import timedelta

import pytest
from tests.fixtures.scheduler_fixtures import utc_at

from app.scheduler.rules import IntervalRule

pytestmark = pytest.mark.unit


def test_interval_rule_due_when_never_run() -> None:
    rule = IntervalRule(interval_seconds=60)
    assert rule.is_due(utc_at(2024, 1, 1, 0, 0), None) is True


def test_interval_rule_not_due_before_interval_elapsed() -> None:
    rule = IntervalRule(interval_seconds=60)
    last_run = utc_at(2024, 1, 1, 0, 0)
    now = last_run + timedelta(seconds=30)
    assert rule.is_due(now, last_run) is False


def test_interval_rule_due_after_interval_elapsed() -> None:
    rule = IntervalRule(interval_seconds=60)
    last_run = utc_at(2024, 1, 1, 0, 0)
    now = last_run + timedelta(seconds=60)
    assert rule.is_due(now, last_run) is True
