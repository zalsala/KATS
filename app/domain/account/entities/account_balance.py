"""Account balance domain entity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.domain.account.value_objects.account_context import AccountContext


@dataclass(frozen=True, slots=True)
class AccountBalance:
    """Account balance summary."""

    account: AccountContext
    total_evaluation_amount: Decimal
    total_purchase_amount: Decimal
    total_profit_loss_amount: Decimal
    total_profit_loss_rate: Decimal
    queried_at: datetime
