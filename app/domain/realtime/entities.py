"""Realtime domain entities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class RealtimePrice:
    """Realtime stock price tick."""

    symbol_code: str
    price: str
    trade_time: str
    received_at: datetime


@dataclass(slots=True)
class RealtimeOrderbook:
    """Realtime top-of-book snapshot."""

    symbol_code: str
    ask_price: str
    ask_volume: str
    bid_price: str
    bid_volume: str
    received_at: datetime


@dataclass(slots=True)
class ExecutionNotice:
    """Realtime order execution notice."""

    symbol_code: str
    order_number: str
    executed_quantity: str
    executed_price: str
    side: str
    received_at: datetime
