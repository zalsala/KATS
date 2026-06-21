"""Trade history domain entity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.domain.account.value_objects.account_context import AccountContext


@dataclass(frozen=True, slots=True)
class TradeHistory:
    """Single trade execution record."""

    account: AccountContext
    order_date: str
    order_time: str
    symbol_code: str
    stock_name: str
    side: str
    executed_quantity: Decimal
    executed_price: Decimal
    executed_amount: Decimal
    order_number: str
    queried_at: datetime
