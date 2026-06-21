"""Strategy execution result DTO."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.dto.strategy.signal_dto import SignalDto


class StrategyResultDto(BaseModel):
    """DTO for strategy execution output."""

    strategy_id: str = ""
    strategy_name: str = ""
    evaluated: bool = False
    accepted: bool = False
    message: str = ""
    signal: SignalDto | None = None
    statistics: dict[str, int] = Field(default_factory=dict)
