"""SchedulerService tests."""

from __future__ import annotations

import pytest
from tests.fixtures.scheduler_fixtures import (
    build_interval_task,
    build_test_event_bus_service,
    build_test_scheduler_service,
    utc_at,
)

from app.events.event_types import EventType
from app.service.portfolio.portfolio_service import PortfolioService
from app.service.scheduler.scheduler_service import SchedulerService, build_scheduler_service

pytestmark = pytest.mark.unit


def test_scheduler_service_register_and_list_tasks() -> None:
    service = build_test_scheduler_service()
    service.register_task(build_interval_task(task_id="task-a"))
    tasks = service.list_tasks()
    assert len(tasks) == 1
    assert tasks[0]["task_id"] == "task-a"


def test_scheduler_service_start_requires_event_bus() -> None:
    service = SchedulerService()
    with pytest.raises(ValueError, match="EventBusService"):
        service.start()


def test_scheduler_service_publishes_system_event_on_tick() -> None:
    event_bus = build_test_event_bus_service()
    captured: list[str] = []

    def _capture(event: object) -> None:
        captured.append(getattr(event, "event_name", ""))

    event_bus.subscribe(EventType.SYSTEM, _capture)
    service = build_scheduler_service(
        event_bus=event_bus,
        portfolio_service=PortfolioService(account_no="evt-account"),
    )
    service.start(event_bus)
    service.register_task(build_interval_task(task_id="evt-task"))
    service.tick(now=utc_at(2024, 1, 1, 0, 0))
    assert any(name == "scheduler.task.completed" for name in captured)


def test_failed_task_is_logged_and_scheduler_continues() -> None:
    from app.scheduler.scheduled_task import ScheduledTask
    from app.scheduler.task_types import ScheduledTaskType

    service = build_test_scheduler_service(
        portfolio_service=PortfolioService(account_no="continue-account")
    )
    service.register_task(
        ScheduledTask(
            task_id="bad-start",
            task_type=ScheduledTaskType.STRATEGY_AUTO_START,
            rule=build_interval_task().rule,
            payload={"strategy_id": ""},
        )
    )
    service.register_task(build_interval_task(task_id="good-task"))
    results = service.tick(now=utc_at(2024, 1, 1, 0, 0))
    assert len(results) == 2
    assert results[0].success is False
    assert results[1].success is True
