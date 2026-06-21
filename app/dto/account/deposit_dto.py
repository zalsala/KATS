"""Deposit DTO."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class DepositDto(BaseModel):
    """DTO for deposit (cash) fields."""

    total_deposit_amount: str = ""
    orderable_cash_amount: str = ""
    next_day_withdrawable_amount: str = ""

    @classmethod
    def from_api_output(cls, output: dict[str, Any]) -> DepositDto:
        """Build DTO from KIS balance ``output`` deposit fields."""
        return cls(
            total_deposit_amount=str(output.get("dnca_tot_amt", "")),
            orderable_cash_amount=str(output.get("ord_psbl_cash", "")),
            next_day_withdrawable_amount=str(output.get("nxdy_excc_amt", "")),
        )
