"""Task execution result model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.scheduler.task_types import ScheduledTaskType


@dataclass(frozen=True, slots=True)
class TaskExecutionResult:
    """Outcome of a single scheduled task execution."""

    task_id: str
    task_type: ScheduledTaskType
    success: bool
    skipped: bool = False
    message: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    executed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
