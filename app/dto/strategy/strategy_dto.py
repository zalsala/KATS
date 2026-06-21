"""Strategy DTO."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class StrategyDto(BaseModel):
    """DTO for strategy metadata."""

    strategy_id: str = ""
    name: str = ""
    strategy_type: str = ""
    enabled: bool = True
    parameters: dict[str, Any] = Field(default_factory=dict)
    symbols: list[str] = Field(default_factory=list)
    state: str = "created"
