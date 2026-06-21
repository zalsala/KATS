"""Order response DTO."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class OrderResponse(BaseModel):
    """DTO for order submission API output."""

    order_branch: str = ""
    order_number: str = ""
    order_time: str = ""

    @classmethod
    def from_api_output(cls, output: dict[str, Any]) -> OrderResponse:
        """Build DTO from KIS order output."""
        return cls(
            order_branch=str(
                output.get("KRX_FWDG_ORD_ORGNO", output.get("krx_fwdg_ord_orgno", ""))
            ),
            order_number=str(output.get("ODNO", output.get("odno", ""))),
            order_time=str(output.get("ORD_TMD", output.get("ord_tmd", ""))),
        )
