"""Market price inquiry DTOs."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class InquirePriceRequestDto(BaseModel):
    """Request DTO for domestic stock current price inquiry.

    Attributes:
        fid_cond_mrkt_div_code: Market division code. ``J`` for KRX.
        fid_input_iscd: Stock symbol code.
    """

    fid_cond_mrkt_div_code: str = "J"
    fid_input_iscd: str

    def to_params(self) -> dict[str, str]:
        """Convert to KIS REST query parameters."""
        return {
            "FID_COND_MRKT_DIV_CODE": self.fid_cond_mrkt_div_code,
            "FID_INPUT_ISCD": self.fid_input_iscd,
        }


class InquirePriceResponseDto(BaseModel):
    """Response DTO for domestic stock current price inquiry."""

    stock_code: str = ""
    stock_name: str = ""
    current_price: str = ""
    change_amount: str = ""
    change_rate: str = ""

    @classmethod
    def from_api_output(cls, output: dict[str, Any]) -> InquirePriceResponseDto:
        """Build DTO from KIS ``output`` section.

        Args:
            output: Parsed ``output`` dictionary from KIS REST response.

        Returns:
            Normalized price response DTO.
        """
        return cls(
            stock_code=str(output.get("mksc_shrn_iscd", output.get("stck_shrn_iscd", ""))),
            stock_name=str(output.get("hts_kor_isnm", "")),
            current_price=str(output.get("stck_prpr", "")),
            change_amount=str(output.get("prdy_vrss", "")),
            change_rate=str(output.get("prdy_ctrt", "")),
        )
