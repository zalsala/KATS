"""Account repository interface."""

from __future__ import annotations

from typing import Protocol

from app.domain.account.entities.account_balance import AccountBalance
from app.domain.account.entities.deposit import Deposit
from app.domain.account.entities.holding_stock import HoldingStock
from app.domain.account.entities.orderable_amount import OrderableAmount
from app.domain.account.entities.trade_history import TradeHistory
from app.domain.account.value_objects.account_context import AccountContext


class IAccountRepository(Protocol):
    """Account data access interface."""

    def get_account_balance(self, account: AccountContext) -> AccountBalance:
        """Return account balance summary."""
        ...

    def get_deposit(self, account: AccountContext) -> Deposit:
        """Return deposit (cash) summary."""
        ...

    def get_holding_stocks(self, account: AccountContext) -> list[HoldingStock]:
        """Return held stock positions."""
        ...

    def get_orderable_amount(
        self,
        account: AccountContext,
        *,
        symbol_code: str,
        price: str = "0",
    ) -> OrderableAmount:
        """Return orderable cash and quantity for a symbol."""
        ...

    def get_trade_history(
        self,
        account: AccountContext,
        *,
        start_date: str,
        end_date: str,
        symbol_code: str = "",
    ) -> list[TradeHistory]:
        """Return daily trade execution history."""
        ...
