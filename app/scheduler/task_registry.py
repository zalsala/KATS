"""Scheduled task registry."""

from __future__ import annotations

from app.scheduler.scheduled_task import ScheduledTask


class TaskRegistry:
    """In-memory registry of scheduled tasks."""

    def __init__(self) -> None:
        self._tasks: dict[str, ScheduledTask] = {}

    def register(self, task: ScheduledTask) -> None:
        """Register or replace a scheduled task."""
        self._tasks[task.task_id] = task

    def unregister(self, task_id: str) -> bool:
        """Remove a task by id."""
        return self._tasks.pop(task_id, None) is not None

    def get(self, task_id: str) -> ScheduledTask | None:
        """Return a task by id."""
        return self._tasks.get(task_id)

    def list_all(self) -> tuple[ScheduledTask, ...]:
        """Return all registered tasks."""
        return tuple(self._tasks.values())

    def list_enabled(self) -> tuple[ScheduledTask, ...]:
        """Return enabled tasks only."""
        return tuple(task for task in self._tasks.values() if task.enabled)

    def is_registered(self, task_id: str) -> bool:
        """Return whether a task id exists."""
        return task_id in self._tasks
