"""Account service and use case tests."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from tests.fixtures.account_fixtures import sample_account_context

from app.domain.account.entities.account_balance import AccountBalance
from app.domain.account.entities.deposit import Deposit
from app.domain.account.entities.holding_stock import HoldingStock
from app.domain.account.entities.orderable_amount import OrderableAmount
from app.domain.account.entities.trade_history import TradeHistory
from app.domain.account.value_objects.account_context import AccountContext
from app.repository.interfaces.account_repository import IAccountRepository
from app.service.account.account_service import AccountService
from app.service.account.usecases.account_use_cases import (
    GetAccountBalanceUseCase,
    GetDepositUseCase,
    GetHoldingStocksUseCase,
    GetOrderableAmountUseCase,
    GetTradeHistoryUseCase,
)

pytestmark = pytest.mark.unit


class FakeAccountRepository:
    """Fake account repository for service tests."""

    def get_account_balance(self, account: AccountContext) -> AccountBalance:
        return AccountBalance(
            account=account,
            total_evaluation_amount=Decimal("1"),
            total_purchase_amount=Decimal("1"),
            total_profit_loss_amount=Decimal("0"),
            total_profit_loss_rate=Decimal("0"),
            queried_at=datetime.now(UTC),
        )

    def get_deposit(self, account: AccountContext) -> Deposit:
        return Deposit(
            account=account,
            total_deposit_amount=Decimal("2"),
            orderable_cash_amount=Decimal("1"),
            next_day_withdrawable_amount=Decimal("1"),
            queried_at=datetime.now(UTC),
        )

    def get_holding_stocks(self, account: AccountContext) -> list[HoldingStock]:
        return [
            HoldingStock(
                account=account,
                symbol_code="005930",
                stock_name="삼성전자",
                quantity=Decimal("1"),
                average_price=Decimal("1"),
                current_price=Decimal("1"),
                evaluation_amount=Decimal("1"),
                profit_loss_amount=Decimal("0"),
                profit_loss_rate=Decimal("0"),
                queried_at=datetime.now(UTC),
            )
        ]

    def get_orderable_amount(
        self,
        account: AccountContext,
        *,
        symbol_code: str,
        price: str = "0",
    ) -> OrderableAmount:
        _ = price
        return OrderableAmount(
            account=account,
            symbol_code=symbol_code,
            orderable_cash=Decimal("100"),
            orderable_quantity=Decimal("1"),
            max_buy_amount=Decimal("100"),
            queried_at=datetime.now(UTC),
        )

    def get_trade_history(
        self,
        account: AccountContext,
        *,
        start_date: str,
        end_date: str,
        symbol_code: str = "",
    ) -> list[TradeHistory]:
        _ = (start_date, end_date, symbol_code)
        return [
            TradeHistory(
                account=account,
                order_date="20260620",
                order_time="093000",
                symbol_code="005930",
                stock_name="삼성전자",
                side="02",
                executed_quantity=Decimal("1"),
                executed_price=Decimal("70000"),
                executed_amount=Decimal("70000"),
                order_number="1",
                queried_at=datetime.now(UTC),
            )
        ]


class TestAccountUseCases:
    """Tests for account use cases."""

    def test_use_cases_delegate_to_repository(self) -> None:
        repository: IAccountRepository = FakeAccountRepository()
        account = sample_account_context()

        balance = GetAccountBalanceUseCase(repository).execute(account)
        deposit = GetDepositUseCase(repository).execute(account)
        holdings = GetHoldingStocksUseCase(repository).execute(account)
        orderable = GetOrderableAmountUseCase(repository).execute(account, symbol_code="005930")
        history = GetTradeHistoryUseCase(repository).execute(
            account,
            start_date="20260601",
            end_date="20260620",
        )

        assert balance.total_evaluation_amount == Decimal("1")
        assert deposit.total_deposit_amount == Decimal("2")
        assert len(holdings) == 1
        assert orderable.symbol_code == "005930"
        assert len(history) == 1


class TestAccountService:
    """Tests for AccountService."""

    def test_service_orchestrates_all_account_features(self) -> None:
        repository: IAccountRepository = FakeAccountRepository()
        service = AccountService(account_repository=repository)
        account = sample_account_context()

        assert service.get_account_balance(account).total_evaluation_amount == Decimal("1")
        assert service.get_deposit(account).total_deposit_amount == Decimal("2")
        assert len(service.get_holding_stocks(account)) == 1
        assert service.get_orderable_amount(
            account, symbol_code="005930"
        ).orderable_cash == Decimal("100")
        assert (
            len(
                service.get_trade_history(
                    account,
                    start_date="20260601",
                    end_date="20260620",
                )
            )
            == 1
        )
