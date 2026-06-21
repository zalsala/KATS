"""Daily time schedule rule."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo


@dataclass(frozen=True, slots=True)
class DailyTimeRule:
    """Run a task once per day at a specific local time."""

    hour: int
    minute: int = 0
    timezone: str = "Asia/Seoul"
    _tzinfo: ZoneInfo = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not 0 <= self.hour <= 23:
            msg = "hour must be between 0 and 23"
            raise ValueError(msg)
        if not 0 <= self.minute <= 59:
            msg = "minute must be between 0 and 59"
            raise ValueError(msg)
        object.__setattr__(self, "_tzinfo", ZoneInfo(self.timezone))

    def is_due(self, now: datetime, last_run_at: datetime | None) -> bool:
        local_now = now.astimezone(self._tzinfo)
        scheduled = local_now.replace(
            hour=self.hour,
            minute=self.minute,
            second=0,
            microsecond=0,
        )
        if local_now < scheduled:
            return False
        if last_run_at is None:
            return True
        last_local = last_run_at.astimezone(self._tzinfo)
        return last_local.date() < local_now.date() or last_local < scheduled
