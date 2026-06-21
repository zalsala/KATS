"""Strategy entity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.strategy.strategy_state import StrategyState
from app.domain.strategy.strategy_statistics import StrategyStatistics


@dataclass(slots=True)
class Strategy:
    """Registered strategy metadata and runtime state."""

    strategy_id: str
    name: str
    strategy_type: str
    enabled: bool
    parameters: dict[str, Any]
    symbols: tuple[str, ...]
    state: StrategyState = StrategyState.CREATED
    statistics: StrategyStatistics | None = None

    def __post_init__(self) -> None:
        if self.statistics is None:
            self.statistics = StrategyStatistics(strategy_id=self.strategy_id)
