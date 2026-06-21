"""Account balance DTO."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class AccountBalanceDto(BaseModel):
    """DTO for account balance summary fields."""

    total_evaluation_amount: str = ""
    total_purchase_amount: str = ""
    total_profit_loss_amount: str = ""
    total_profit_loss_rate: str = ""

    @classmethod
    def from_api_output(cls, output: dict[str, Any]) -> AccountBalanceDto:
        """Build DTO from KIS balance ``output`` section."""
        return cls(
            total_evaluation_amount=str(output.get("tot_evlu_amt", "")),
            total_purchase_amount=str(output.get("pchs_amt_smtl_amt", "")),
            total_profit_loss_amount=str(output.get("evlu_pfls_smtl_amt", "")),
            total_profit_loss_rate=str(output.get("evlu_pfls_rt", "")),
        )
