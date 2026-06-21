"""Market session schedule rule."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Literal
from zoneinfo import ZoneInfo

MarketEvent = Literal["open", "close"]


@dataclass(frozen=True, slots=True)
class MarketTimeRule:
    """Run a task at market open or close on trading weekdays."""

    market_event: MarketEvent
    timezone: str = "Asia/Seoul"
    open_time: time = time(hour=9, minute=0)
    close_time: time = time(hour=15, minute=30)
    _tzinfo: ZoneInfo = field(init=False, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_tzinfo", ZoneInfo(self.timezone))

    def is_due(self, now: datetime, last_run_at: datetime | None) -> bool:
        local_now = now.astimezone(self._tzinfo)
        if local_now.weekday() >= 5:
            return False

        target = self.open_time if self.market_event == "open" else self.close_time
        scheduled = local_now.replace(
            hour=target.hour,
            minute=target.minute,
            second=0,
            microsecond=0,
        )
        if local_now < scheduled:
            return False
        if last_run_at is None:
            return True
        last_local = last_run_at.astimezone(self._tzinfo)
        if last_local.date() != local_now.date():
            return True
        return last_local < scheduled
