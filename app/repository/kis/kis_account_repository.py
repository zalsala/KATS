"""KIS account repository implementation."""

from __future__ import annotations

import logging

from app.broker.kis.api.account_api_keys import (
    INQUIRE_BALANCE,
    INQUIRE_DAILY_CCLD,
    INQUIRE_PSBL_ORDER,
)
from app.broker.kis.rest.api_result import ApiResult
from app.domain.account.entities.account_balance import AccountBalance
from app.domain.account.entities.deposit import Deposit
from app.domain.account.entities.holding_stock import HoldingStock
from app.domain.account.entities.orderable_amount import OrderableAmount
from app.domain.account.entities.trade_history import TradeHistory
from app.domain.account.value_objects.account_context import AccountContext
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
from app.dto.account.orderable_amount_dto import OrderableAmountDto, OrderableAmountRequestDto
from app.dto.account.trade_history_dto import TradeHistoryDto, TradeHistoryRequestDto
from app.repository.kis.account_api_client import AccountApiClient

logger = logging.getLogger(__name__)

BALANCE_QUERY_PARAMS = {
    "AFHR_FLPR_YN": "N",
    "OFL_YN": "",
    "INQR_DVSN": "02",
    "UNPR_DVSN": "01",
    "FUND_STTL_ICLD_YN": "N",
    "FNCG_AMT_AUTO_RDPT_YN": "N",
    "PRCS_DVSN": "01",
    "CTX_AREA_FK100": "",
    "CTX_AREA_NK100": "",
}


class KisAccountRepository:
    """Account repository using ``AccountApiClient`` and DTO mappers."""

    def __init__(self, *, account_api_client: AccountApiClient) -> None:
        """Initialize repository dependencies."""
        self._client = account_api_client

    def get_account_balance(self, account: AccountContext) -> AccountBalance:
        """Return account balance summary."""
        result = self._fetch_balance(account)
        dto = AccountBalanceDto.from_api_output(result.output)
        return AccountBalanceMapper.to_entity(dto, account=account)

    def get_deposit(self, account: AccountContext) -> Deposit:
        """Return deposit summary from balance inquiry."""
        result = self._fetch_balance(account)
        dto = DepositDto.from_api_output(result.output)
        return DepositMapper.to_entity(dto, account=account)

    def get_holding_stocks(self, account: AccountContext) -> list[HoldingStock]:
        """Return held stocks from balance inquiry."""
        result = self._fetch_balance(account)
        dtos = HoldingStockDto.from_api_output1(result.output1)
        return HoldingStockMapper.to_entities(dtos, account=account)

    def get_orderable_amount(
        self,
        account: AccountContext,
        *,
        symbol_code: str,
        price: str = "0",
    ) -> OrderableAmount:
        """Return orderable amount for a symbol."""
        request = OrderableAmountRequestDto(
            account=account,
            symbol_code=symbol_code,
            price=price,
        )
        result = self._client.get(INQUIRE_PSBL_ORDER, request.to_params())
        dto = OrderableAmountDto.from_api_output(result.output)
        return OrderableAmountMapper.to_entity(dto, account=account)

    def get_trade_history(
        self,
        account: AccountContext,
        *,
        start_date: str,
        end_date: str,
        symbol_code: str = "",
    ) -> list[TradeHistory]:
        """Return daily trade execution history."""
        request = TradeHistoryRequestDto(
            account=account,
            start_date=start_date,
            end_date=end_date,
            symbol_code=symbol_code,
        )
        result = self._client.get(INQUIRE_DAILY_CCLD, request.to_params())
        dtos = TradeHistoryDto.from_api_output1(result.output1)
        return TradeHistoryMapper.to_entities(dtos, account=account)

    def _fetch_balance(self, account: AccountContext) -> ApiResult:
        params = account.to_base_params()
        params.update(BALANCE_QUERY_PARAMS)
        logger.info("Fetching account balance for CANO=%s", account.account_no)
        return self._client.get(INQUIRE_BALANCE, params)
