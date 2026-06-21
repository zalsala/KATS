"""Orderable amount DTO."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.dto.account.account_request_base import AccountRequestBase


class OrderableAmountRequestDto(AccountRequestBase):
    """Request DTO for orderable amount inquiry."""

    symbol_code: str
    price: str
    order_division: str = Field(default="00", description="00: limit order")
    quantity: str = "1"

    def to_params(self) -> dict[str, str]:
        """Convert to KIS REST query parameters."""
        params = self.base_params()
        params.update(
            {
                "PDNO": self.symbol_code,
                "ORD_DVSN": self.order_division,
                "ORD_UNPR": self.price,
                "ORD_QTY": self.quantity,
                "CMA_EVLU_AMT_ICLD_YN": "Y",
                "OVRS_ICLD_YN": "N",
            }
        )
        return params


class OrderableAmountDto(BaseModel):
    """DTO for orderable amount response."""

    symbol_code: str = ""
    orderable_cash: str = ""
    orderable_quantity: str = ""
    max_buy_amount: str = ""

    @classmethod
    def from_api_output(cls, output: dict[str, Any]) -> OrderableAmountDto:
        """Build DTO from KIS ``inquire-psbl-order`` output."""
        return cls(
            symbol_code=str(output.get("pdno", "")),
            orderable_cash=str(output.get("ord_psbl_cash", "")),
            orderable_quantity=str(output.get("max_buy_qty", "")),
            max_buy_amount=str(output.get("max_buy_amt", "")),
        )
