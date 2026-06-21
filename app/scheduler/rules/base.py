"""Schedule rule protocol."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol


class ScheduleRule(Protocol):
    """Protocol for determining when a scheduled task is due."""

    def is_due(self, now: datetime, last_run_at: datetime | None) -> bool:
        """Return whether the task should run at ``now``."""
