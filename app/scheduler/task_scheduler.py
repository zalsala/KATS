"""Task scheduling engine."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from app.scheduler.scheduled_task import ScheduledTask
from app.scheduler.task_execution_result import TaskExecutionResult
from app.scheduler.task_executor import TaskExecutor
from app.scheduler.task_registry import TaskRegistry
from app.scheduler.task_types import ScheduledTaskType


def _resolve_logger() -> logging.Logger:
    return logging.getLogger(__name__)


class TaskScheduler:
    """Evaluate due tasks and execute them without duplicate overlap."""

    def __init__(
        self,
        *,
        registry: TaskRegistry,
        executor: TaskExecutor,
    ) -> None:
        self._registry = registry
        self._executor = executor
        self._running: set[str] = set()
        self._logger = _resolve_logger()

    @property
    def running_task_ids(self) -> frozenset[str]:
        """Return task ids currently executing."""
        return frozenset(self._running)

    def tick(self, *, now: datetime | None = None) -> list[TaskExecutionResult]:
        """Evaluate all enabled tasks and execute those that are due."""
        current_time = now or datetime.now(UTC)
        results: list[TaskExecutionResult] = []
        for task in self._registry.list_enabled():
            if not task.rule.is_due(current_time, task.last_run_at):
                continue
            result = self._execute_task(task, current_time)
            results.append(result)
        return results

    def execute_task(self, task_id: str, *, now: datetime | None = None) -> TaskExecutionResult:
        """Execute a single task immediately if it is registered."""
        task = self._registry.get(task_id)
        if task is None:
            return TaskExecutionResult(
                task_id=task_id,
                task_type=ScheduledTaskType.LOG_CLEANUP,
                success=False,
                message="task not found",
            )
        return self._execute_task(task, now or datetime.now(UTC))

    def _execute_task(self, task: ScheduledTask, now: datetime) -> TaskExecutionResult:
        if task.task_id in self._running:
            self._logger.info("Skipping duplicate execution for task_id=%s", task.task_id)
            return TaskExecutionResult(
                task_id=task.task_id,
                task_type=task.task_type,
                success=True,
                skipped=True,
                message="duplicate execution prevented",
            )

        self._running.add(task.task_id)
        try:
            result = self._executor.execute(task)
            if not result.skipped:
                task.mark_executed(now)
            return result
        finally:
            self._running.discard(task.task_id)
