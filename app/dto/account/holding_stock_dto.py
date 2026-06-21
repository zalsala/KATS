"""Holding stock DTO."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class HoldingStockDto(BaseModel):
    """DTO for a single held stock row."""

    symbol_code: str = ""
    stock_name: str = ""
    quantity: str = ""
    average_price: str = ""
    current_price: str = ""
    evaluation_amount: str = ""
    profit_loss_amount: str = ""
    profit_loss_rate: str = ""

    @classmethod
    def from_api_row(cls, row: dict[str, Any]) -> HoldingStockDto:
        """Build DTO from KIS balance ``output1`` row."""
        return cls(
            symbol_code=str(row.get("pdno", "")),
            stock_name=str(row.get("prdt_name", "")),
            quantity=str(row.get("hldg_qty", "")),
            average_price=str(row.get("pchs_avg_pric", "")),
            current_price=str(row.get("prpr", "")),
            evaluation_amount=str(row.get("evlu_amt", "")),
            profit_loss_amount=str(row.get("evlu_pfls_amt", "")),
            profit_loss_rate=str(row.get("evlu_pfls_rt", "")),
        )

    @classmethod
    def from_api_output1(cls, rows: list[dict[str, Any]]) -> list[HoldingStockDto]:
        """Build DTO list from ``output1`` rows."""
        return [cls.from_api_row(row) for row in rows if isinstance(row, dict)]
