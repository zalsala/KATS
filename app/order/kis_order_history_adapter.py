"""KIS domestic order history adapter."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.domain.account.value_objects.account_context import AccountContext
from app.domain.trade_blotter.trade_blotter_item import TradeBlotterItem
from app.dto.account.trade_history_dto import TradeHistoryDto
from app.service.account.account_service import AccountService

KIS_TIMEZONE = ZoneInfo("Asia/Seoul")


class KISOrderHistoryAdapter:
    """Adapter for KIS domestic stock daily order and execution inquiry."""

    def __init__(self, *, account_service: AccountService) -> None:
        self._account_service = account_service

    def get_order_history(
        self,
        account: AccountContext,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        symbol_code: str = "",
    ) -> list[TradeBlotterItem]:
        """Return normalized order history rows for the requested date range."""
        inquiry_start, inquiry_end = _resolve_date_range(start_date, end_date)
        rows = self._account_service.get_trade_history(
            account,
            start_date=inquiry_start,
            end_date=inquiry_end,
            symbol_code=symbol_code,
        )
        dtos = [
            TradeHistoryDto(
                order_date=row.order_date,
                order_time=row.order_time,
                symbol_code=row.symbol_code,
                stock_name=row.stock_name,
                side=row.side,
                executed_quantity=str(row.executed_quantity),
                executed_price=str(row.executed_price),
                executed_amount=str(row.executed_amount),
                order_number=row.order_number,
            )
            for row in rows
        ]
        items = [TradeBlotterItem.from_trade_history_dto(dto) for dto in dtos]
        return sorted(items, key=lambda item: item.sort_key, reverse=True)


def _resolve_date_range(
    start_date: str | None,
    end_date: str | None,
) -> tuple[str, str]:
    today = datetime.now(KIS_TIMEZONE).strftime("%Y%m%d")
    return start_date or today, end_date or today
