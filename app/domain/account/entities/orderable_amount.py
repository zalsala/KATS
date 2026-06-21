"""Orderable amount domain entity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.domain.account.value_objects.account_context import AccountContext


@dataclass(frozen=True, slots=True)
class OrderableAmount:
    """Orderable cash and quantity for a symbol."""

    account: AccountContext
    symbol_code: str
    orderable_cash: Decimal
    orderable_quantity: Decimal
    max_buy_amount: Decimal
    queried_at: datetime
