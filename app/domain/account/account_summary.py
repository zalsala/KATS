"""Normalized domestic stock account summary for the UI."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.domain.account.entities.account_balance import AccountBalance
from app.domain.account.entities.deposit import Deposit
from app.domain.position.position_item import PositionItem


@dataclass(frozen=True, slots=True)
class AccountSummary:
    """Account-level cash and valuation summary."""

    cash_balance: Decimal
    available_buying_power: Decimal
    total_evaluation_amount: Decimal
    total_purchase_amount: Decimal
    total_profit_loss_amount: Decimal
    total_profit_loss_rate: Decimal
    last_refreshed_at: datetime

    @classmethod
    def from_balance_and_deposit(
        cls,
        *,
        balance: AccountBalance,
        deposit: Deposit,
    ) -> AccountSummary:
        """Build a summary from KIS balance inquiry entities."""
        return cls(
            cash_balance=deposit.total_deposit_amount,
            available_buying_power=deposit.orderable_cash_amount,
            total_evaluation_amount=balance.total_evaluation_amount,
            total_purchase_amount=balance.total_purchase_amount,
            total_profit_loss_amount=balance.total_profit_loss_amount,
            total_profit_loss_rate=balance.total_profit_loss_rate,
            last_refreshed_at=balance.queried_at,
        )

    def with_positions(self, positions: list[PositionItem]) -> AccountSummary:
        """Recalculate stock valuation metrics from updated holdings."""
        stock_evaluation = sum((position.evaluation_amount for position in positions), Decimal("0"))
        total_evaluation = self.cash_balance + stock_evaluation
        total_profit_loss = stock_evaluation - self.total_purchase_amount
        if self.total_purchase_amount > 0:
            total_profit_loss_rate = (total_profit_loss / self.total_purchase_amount) * Decimal(
                "100"
            )
        else:
            total_profit_loss_rate = Decimal("0")
        return AccountSummary(
            cash_balance=self.cash_balance,
            available_buying_power=self.available_buying_power,
            total_evaluation_amount=total_evaluation,
            total_purchase_amount=self.total_purchase_amount,
            total_profit_loss_amount=total_profit_loss,
            total_profit_loss_rate=total_profit_loss_rate,
            last_refreshed_at=self.last_refreshed_at,
        )
