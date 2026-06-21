"""Scheduled task model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.scheduler.rules.base import ScheduleRule
from app.scheduler.task_types import ScheduledTaskType


@dataclass(slots=True)
class ScheduledTask:
    """A task registered with the scheduler."""

    task_id: str
    task_type: ScheduledTaskType
    rule: ScheduleRule
    payload: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    last_run_at: datetime | None = None
    description: str = ""

    def mark_executed(self, executed_at: datetime | None = None) -> None:
        """Record the latest execution timestamp."""
        self.last_run_at = executed_at or datetime.now(UTC)
