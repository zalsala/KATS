"""Trading signal DTO."""

from __future__ import annotations

from pydantic import BaseModel


class SignalDto(BaseModel):
    """DTO for a trading signal."""

    signal_id: str = ""
    strategy_id: str = ""
    strategy_name: str = ""
    symbol_code: str = ""
    signal_type: str = ""
    price: str = "0"
    quantity: str = "0"
    confidence: str = "0"
    timestamp: str = ""
    reason: str = ""
