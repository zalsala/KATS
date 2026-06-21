"""Account use cases."""

from __future__ import annotations

from app.domain.account.entities.account_balance import AccountBalance
from app.domain.account.entities.deposit import Deposit
from app.domain.account.entities.holding_stock import HoldingStock
from app.domain.account.entities.orderable_amount import OrderableAmount
from app.domain.account.entities.trade_history import TradeHistory
from app.domain.account.value_objects.account_context import AccountContext
from app.repository.interfaces.account_repository import IAccountRepository


class GetAccountBalanceUseCase:
    """Retrieve account balance summary."""

    def __init__(self, account_repository: IAccountRepository) -> None:
        self._account_repository = account_repository

    def execute(self, account: AccountContext) -> AccountBalance:
        return self._account_repository.get_account_balance(account)


class GetDepositUseCase:
    """Retrieve deposit summary."""

    def __init__(self, account_repository: IAccountRepository) -> None:
        self._account_repository = account_repository

    def execute(self, account: AccountContext) -> Deposit:
        return self._account_repository.get_deposit(account)


class GetHoldingStocksUseCase:
    """Retrieve held stock positions."""

    def __init__(self, account_repository: IAccountRepository) -> None:
        self._account_repository = account_repository

    def execute(self, account: AccountContext) -> list[HoldingStock]:
        return self._account_repository.get_holding_stocks(account)


class GetOrderableAmountUseCase:
    """Retrieve orderable amount for a symbol."""

    def __init__(self, account_repository: IAccountRepository) -> None:
        self._account_repository = account_repository

    def execute(
        self,
        account: AccountContext,
        *,
        symbol_code: str,
        price: str = "0",
    ) -> OrderableAmount:
        return self._account_repository.get_orderable_amount(
            account,
            symbol_code=symbol_code,
            price=price,
        )


class GetTradeHistoryUseCase:
    """Retrieve daily trade execution history."""

    def __init__(self, account_repository: IAccountRepository) -> None:
        self._account_repository = account_repository

    def execute(
        self,
        account: AccountContext,
        *,
        start_date: str,
        end_date: str,
        symbol_code: str = "",
    ) -> list[TradeHistory]:
        return self._account_repository.get_trade_history(
            account,
            start_date=start_date,
            end_date=end_date,
            symbol_code=symbol_code,
        )
