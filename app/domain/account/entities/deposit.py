"""Deposit domain entity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.domain.account.value_objects.account_context import AccountContext


@dataclass(frozen=True, slots=True)
class Deposit:
    """Cash deposit summary."""

    account: AccountContext
    total_deposit_amount: Decimal
    orderable_cash_amount: Decimal
    next_day_withdrawable_amount: Decimal
    queried_at: datetime
