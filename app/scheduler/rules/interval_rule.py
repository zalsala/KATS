"""Fixed-interval schedule rule."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class IntervalRule:
    """Run a task every N seconds after the previous execution."""

    interval_seconds: int

    def __post_init__(self) -> None:
        if self.interval_seconds <= 0:
            msg = "interval_seconds must be positive"
            raise ValueError(msg)

    def is_due(self, now: datetime, last_run_at: datetime | None) -> bool:
        if last_run_at is None:
            return True
        elapsed = (now - last_run_at).total_seconds()
        return elapsed >= self.interval_seconds
