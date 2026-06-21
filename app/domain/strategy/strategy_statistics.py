"""Strategy runtime statistics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class StrategyStatistics:
    """Aggregated counters for a strategy."""

    strategy_id: str
    total_signals: int = 0
    buy_signals: int = 0
    sell_signals: int = 0
    hold_signals: int = 0
    cancel_signals: int = 0
    execution_count: int = 0
    market_data_count: int = 0
    last_signal_at: datetime | None = None

    def record_signal(self, signal_type: str, *, at: datetime) -> None:
        """Increment counters for a generated signal."""
        self.total_signals += 1
        self.last_signal_at = at
        if signal_type == "BUY":
            self.buy_signals += 1
        elif signal_type == "SELL":
            self.sell_signals += 1
        elif signal_type == "HOLD":
            self.hold_signals += 1
        elif signal_type == "CANCEL":
            self.cancel_signals += 1
