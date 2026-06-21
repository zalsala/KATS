"""Virtual trade record."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class VirtualTrade:
    """Completed virtual trade for performance analysis."""

    trade_id: str
    symbol_code: str
    side: str
    quantity: Decimal
    price: Decimal
    timestamp: datetime
    realized_pnl: Decimal = Decimal("0")
