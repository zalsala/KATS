"""TaskRegistry tests."""

from __future__ import annotations

import pytest
from tests.fixtures.scheduler_fixtures import build_interval_task

from app.scheduler.task_registry import TaskRegistry

pytestmark = pytest.mark.unit


def test_task_register_and_list() -> None:
    registry = TaskRegistry()
    task = build_interval_task(task_id="refresh-1")
    registry.register(task)
    assert registry.is_registered("refresh-1")
    assert len(registry.list_enabled()) == 1


def test_task_unregister() -> None:
    registry = TaskRegistry()
    registry.register(build_interval_task(task_id="refresh-1"))
    assert registry.unregister("refresh-1") is True
    assert registry.is_registered("refresh-1") is False


def test_disabled_tasks_excluded_from_enabled_list() -> None:
    registry = TaskRegistry()
    task = build_interval_task(task_id="disabled-1")
    task.enabled = False
    registry.register(task)
    assert registry.list_all()
    assert registry.list_enabled() == ()
