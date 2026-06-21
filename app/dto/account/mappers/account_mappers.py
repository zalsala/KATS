"""Account DTO mappers."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from app.domain.account.entities.account_balance import AccountBalance
from app.domain.account.entities.deposit import Deposit
from app.domain.account.entities.holding_stock import HoldingStock
from app.domain.account.entities.orderable_amount import OrderableAmount
from app.domain.account.entities.trade_history import TradeHistory
from app.domain.account.value_objects.account_context import AccountContext
from app.dto.account.account_balance_dto import AccountBalanceDto
from app.dto.account.deposit_dto import DepositDto
from app.dto.account.holding_stock_dto import HoldingStockDto
from app.dto.account.orderable_amount_dto import OrderableAmountDto
from app.dto.account.trade_history_dto import TradeHistoryDto


def _to_decimal(value: str) -> Decimal:
    if not value:
        return Decimal("0")
    return Decimal(value.replace(",", ""))


class AccountBalanceMapper:
    """Maps ``AccountBalanceDto`` to ``AccountBalance`` entity."""

    @staticmethod
    def to_entity(
        dto: AccountBalanceDto,
        *,
        account: AccountContext,
        queried_at: datetime | None = None,
    ) -> AccountBalance:
        return AccountBalance(
            account=account,
            total_evaluation_amount=_to_decimal(dto.total_evaluation_amount),
            total_purchase_amount=_to_decimal(dto.total_purchase_amount),
            total_profit_loss_amount=_to_decimal(dto.total_profit_loss_amount),
            total_profit_loss_rate=_to_decimal(dto.total_profit_loss_rate),
            queried_at=queried_at or datetime.now(UTC),
        )


class DepositMapper:
    """Maps ``DepositDto`` to ``Deposit`` entity."""

    @staticmethod
    def to_entity(
        dto: DepositDto,
        *,
        account: AccountContext,
        queried_at: datetime | None = None,
    ) -> Deposit:
        return Deposit(
            account=account,
            total_deposit_amount=_to_decimal(dto.total_deposit_amount),
            orderable_cash_amount=_to_decimal(dto.orderable_cash_amount),
            next_day_withdrawable_amount=_to_decimal(dto.next_day_withdrawable_amount),
            queried_at=queried_at or datetime.now(UTC),
        )


class HoldingStockMapper:
    """Maps ``HoldingStockDto`` list to ``HoldingStock`` entities."""

    @staticmethod
    def to_entities(
        dtos: list[HoldingStockDto],
        *,
        account: AccountContext,
        queried_at: datetime | None = None,
    ) -> list[HoldingStock]:
        timestamp = queried_at or datetime.now(UTC)
        return [
            HoldingStock(
                account=account,
                symbol_code=dto.symbol_code,
                stock_name=dto.stock_name,
                quantity=_to_decimal(dto.quantity),
                average_price=_to_decimal(dto.average_price),
                current_price=_to_decimal(dto.current_price),
                evaluation_amount=_to_decimal(dto.evaluation_amount),
                profit_loss_amount=_to_decimal(dto.profit_loss_amount),
                profit_loss_rate=_to_decimal(dto.profit_loss_rate),
                queried_at=timestamp,
            )
            for dto in dtos
        ]


class OrderableAmountMapper:
    """Maps ``OrderableAmountDto`` to ``OrderableAmount`` entity."""

    @staticmethod
    def to_entity(
        dto: OrderableAmountDto,
        *,
        account: AccountContext,
        queried_at: datetime | None = None,
    ) -> OrderableAmount:
        return OrderableAmount(
            account=account,
            symbol_code=dto.symbol_code,
            orderable_cash=_to_decimal(dto.orderable_cash),
            orderable_quantity=_to_decimal(dto.orderable_quantity),
            max_buy_amount=_to_decimal(dto.max_buy_amount),
            queried_at=queried_at or datetime.now(UTC),
        )


class TradeHistoryMapper:
    """Maps ``TradeHistoryDto`` list to ``TradeHistory`` entities."""

    @staticmethod
    def to_entities(
        dtos: list[TradeHistoryDto],
        *,
        account: AccountContext,
        queried_at: datetime | None = None,
    ) -> list[TradeHistory]:
        timestamp = queried_at or datetime.now(UTC)
        return [
            TradeHistory(
                account=account,
                order_date=dto.order_date,
                order_time=dto.order_time,
                symbol_code=dto.symbol_code,
                stock_name=dto.stock_name,
                side=dto.side,
                executed_quantity=_to_decimal(dto.executed_quantity),
                executed_price=_to_decimal(dto.executed_price),
                executed_amount=_to_decimal(dto.executed_amount),
                order_number=dto.order_number,
                queried_at=timestamp,
            )
            for dto in dtos
        ]
