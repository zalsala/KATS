"""Duplicate execution prevention tests."""

from __future__ import annotations

import pytest
from tests.fixtures.scheduler_fixtures import (
    build_interval_task,
    build_test_scheduler_service,
    utc_at,
)

from app.scheduler.task_executor import TaskExecutor
from app.scheduler.task_registry import TaskRegistry
from app.scheduler.task_scheduler import TaskScheduler
from app.service.portfolio.portfolio_service import PortfolioService

pytestmark = pytest.mark.unit


def test_duplicate_execution_is_skipped() -> None:
    registry = TaskRegistry()
    task = build_interval_task(task_id="dup-task", interval_seconds=1)
    registry.register(task)

    executor = TaskExecutor()
    scheduler = TaskScheduler(registry=registry, executor=executor)
    scheduler._running.add("dup-task")

    result = scheduler._execute_task(task, utc_at(2024, 1, 1, 0, 0))  # noqa: SLF001
    assert result.skipped is True
    assert "duplicate" in result.message


def test_scheduler_service_tick_marks_last_run_once() -> None:
    service = build_test_scheduler_service(
        portfolio_service=PortfolioService(account_no="dup-account")
    )
    service.register_task(build_interval_task(task_id="refresh-task", interval_seconds=3600))
    first = service.tick(now=utc_at(2024, 1, 1, 0, 0))
    second = service.tick(now=utc_at(2024, 1, 1, 0, 1))
    assert len(first) == 1
    assert first[0].success is True
    assert second == []
