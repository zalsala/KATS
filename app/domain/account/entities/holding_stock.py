"""Holding stock domain entity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.domain.account.value_objects.account_context import AccountContext


@dataclass(frozen=True, slots=True)
class HoldingStock:
    """Single held stock position."""

    account: AccountContext
    symbol_code: str
    stock_name: str
    quantity: Decimal
    average_price: Decimal
    current_price: Decimal
    evaluation_amount: Decimal
    profit_loss_amount: Decimal
    profit_loss_rate: Decimal
    queried_at: datetime
