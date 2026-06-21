"""Strategy statistics DTO."""

from __future__ import annotations

from pydantic import BaseModel


class StatisticsDto(BaseModel):
    """DTO for strategy statistics."""

    strategy_id: str = ""
    total_signals: int = 0
    buy_signals: int = 0
    sell_signals: int = 0
    hold_signals: int = 0
    cancel_signals: int = 0
    execution_count: int = 0
    market_data_count: int = 0
    last_signal_at: str | None = None
