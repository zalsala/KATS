"""Account application service."""

from __future__ import annotations

from app.domain.account.entities.account_balance import AccountBalance
from app.domain.account.entities.deposit import Deposit
from app.domain.account.entities.holding_stock import HoldingStock
from app.domain.account.entities.orderable_amount import OrderableAmount
from app.domain.account.entities.trade_history import TradeHistory
from app.domain.account.value_objects.account_context import AccountContext
from app.repository.interfaces.account_repository import IAccountRepository
from app.service.account.usecases.account_use_cases import (
    GetAccountBalanceUseCase,
    GetDepositUseCase,
    GetHoldingStocksUseCase,
    GetOrderableAmountUseCase,
    GetTradeHistoryUseCase,
)


class AccountService:
    """Application service for account use cases."""

    def __init__(
        self,
        *,
        account_repository: IAccountRepository,
        get_account_balance_use_case: GetAccountBalanceUseCase | None = None,
        get_deposit_use_case: GetDepositUseCase | None = None,
        get_holding_stocks_use_case: GetHoldingStocksUseCase | None = None,
        get_orderable_amount_use_case: GetOrderableAmountUseCase | None = None,
        get_trade_history_use_case: GetTradeHistoryUseCase | None = None,
    ) -> None:
        self._account_repository = account_repository
        self._get_account_balance = get_account_balance_use_case or GetAccountBalanceUseCase(
            account_repository
        )
        self._get_deposit = get_deposit_use_case or GetDepositUseCase(account_repository)
        self._get_holding_stocks = get_holding_stocks_use_case or GetHoldingStocksUseCase(
            account_repository
        )
        self._get_orderable_amount = get_orderable_amount_use_case or GetOrderableAmountUseCase(
            account_repository
        )
        self._get_trade_history = get_trade_history_use_case or GetTradeHistoryUseCase(
            account_repository
        )

    def get_account_balance(self, account: AccountContext) -> AccountBalance:
        return self._get_account_balance.execute(account)

    def get_deposit(self, account: AccountContext) -> Deposit:
        return self._get_deposit.execute(account)

    def get_balance_summary(self, account: AccountContext) -> tuple[Deposit, AccountBalance]:
        """Return deposit and balance summary from a single balance inquiry."""
        return self._account_repository.get_balance_summary(account)

    def get_holding_stocks(self, account: AccountContext) -> list[HoldingStock]:
        return self._get_holding_stocks.execute(account)

    def get_orderable_amount(
        self,
        account: AccountContext,
        *,
        symbol_code: str,
        price: str = "0",
    ) -> OrderableAmount:
        return self._get_orderable_amount.execute(
            account,
            symbol_code=symbol_code,
            price=price,
        )

    def get_trade_history(
        self,
        account: AccountContext,
        *,
        start_date: str,
        end_date: str,
        symbol_code: str = "",
    ) -> list[TradeHistory]:
        return self._get_trade_history.execute(
            account,
            start_date=start_date,
            end_date=end_date,
            symbol_code=symbol_code,
        )


def build_account_service(*, account_repository: IAccountRepository) -> AccountService:
    """Create an ``AccountService`` wired with default use cases."""
    return AccountService(account_repository=account_repository)
