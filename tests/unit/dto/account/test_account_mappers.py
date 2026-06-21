"""DTO mapping tests for account layer."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from tests.fixtures.account_fixtures import sample_account_context

from app.dto.account.account_balance_dto import AccountBalanceDto
from app.dto.account.deposit_dto import DepositDto
from app.dto.account.holding_stock_dto import HoldingStockDto
from app.dto.account.mappers.account_mappers import (
    AccountBalanceMapper,
    DepositMapper,
    HoldingStockMapper,
    OrderableAmountMapper,
    TradeHistoryMapper,
)
from app.dto.account.orderable_amount_dto import OrderableAmountDto
from app.dto.account.trade_history_dto import TradeHistoryDto

pytestmark = pytest.mark.unit


class TestAccountMappers:
    """Tests for account DTO to entity mappers."""

    def test_account_balance_mapper(self) -> None:
        dto = AccountBalanceDto(
            total_evaluation_amount="10000000",
            total_purchase_amount="9000000",
            total_profit_loss_amount="1000000",
            total_profit_loss_rate="11.11",
        )
        account = sample_account_context()
        queried_at = datetime(2026, 6, 20, tzinfo=UTC)

        entity = AccountBalanceMapper.to_entity(dto, account=account, queried_at=queried_at)

        assert entity.total_evaluation_amount == Decimal("10000000")
        assert entity.account.account_no == "12345678"

    def test_deposit_mapper(self) -> None:
        dto = DepositDto(
            total_deposit_amount="2000000",
            orderable_cash_amount="1500000",
            next_day_withdrawable_amount="1800000",
        )

        entity = DepositMapper.to_entity(dto, account=sample_account_context())

        assert entity.orderable_cash_amount == Decimal("1500000")

    def test_holding_stock_mapper(self) -> None:
        dto = HoldingStockDto(
            symbol_code="005930",
            stock_name="삼성전자",
            quantity="10",
            average_price="70000",
            current_price="75000",
            evaluation_amount="750000",
            profit_loss_amount="50000",
            profit_loss_rate="7.14",
        )

        entities = HoldingStockMapper.to_entities([dto], account=sample_account_context())

        assert len(entities) == 1
        assert entities[0].symbol_code == "005930"

    def test_orderable_amount_mapper(self) -> None:
        dto = OrderableAmountDto(
            symbol_code="005930",
            orderable_cash="1500000",
            orderable_quantity="20",
            max_buy_amount="1500000",
        )

        entity = OrderableAmountMapper.to_entity(dto, account=sample_account_context())

        assert entity.orderable_quantity == Decimal("20")

    def test_trade_history_mapper(self) -> None:
        dto = TradeHistoryDto(
            order_date="20260620",
            order_time="093000",
            symbol_code="005930",
            stock_name="삼성전자",
            side="02",
            executed_quantity="1",
            executed_price="70000",
            executed_amount="70000",
            order_number="00001234",
        )

        entities = TradeHistoryMapper.to_entities([dto], account=sample_account_context())

        assert entities[0].order_number == "00001234"
