"""Trade history DTO."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.dto.account.account_request_base import AccountRequestBase


class TradeHistoryRequestDto(AccountRequestBase):
    """Request DTO for daily trade history inquiry."""

    start_date: str
    end_date: str
    symbol_code: str = ""

    def to_params(self) -> dict[str, str]:
        """Convert to KIS REST query parameters."""
        params = self.base_params()
        params.update(
            {
                "INQR_STRT_DT": self.start_date,
                "INQR_END_DT": self.end_date,
                "SLL_BUY_DVSN_CD": "00",
                "INQR_DVSN": "00",
                "PDNO": self.symbol_code,
                "CCLD_DVSN": "00",
                "INQR_DVSN_3": "00",
                "EXCG_DVSN_CD": "KRX",
            }
        )
        return params


class TradeHistoryDto(BaseModel):
    """DTO for a single trade execution row."""

    order_date: str = ""
    order_time: str = ""
    symbol_code: str = ""
    stock_name: str = ""
    side: str = ""
    executed_quantity: str = ""
    executed_price: str = ""
    executed_amount: str = ""
    order_number: str = ""

    @classmethod
    def from_api_row(cls, row: dict[str, Any]) -> TradeHistoryDto:
        """Build DTO from KIS daily ccld ``output1`` row."""
        return cls(
            order_date=str(row.get("ord_dt", "")),
            order_time=str(row.get("ord_tmd", "")),
            symbol_code=str(row.get("pdno", "")),
            stock_name=str(row.get("prdt_name", "")),
            side=str(row.get("sll_buy_dvsn_cd", "")),
            executed_quantity=str(row.get("tot_ccld_qty", "")),
            executed_price=str(row.get("avg_prvs", "")),
            executed_amount=str(row.get("tot_ccld_amt", "")),
            order_number=str(row.get("odno", "")),
        )

    @classmethod
    def from_api_output1(cls, rows: list[dict[str, Any]]) -> list[TradeHistoryDto]:
        """Build DTO list from ``output1`` rows."""
        return [cls.from_api_row(row) for row in rows if isinstance(row, dict)]
