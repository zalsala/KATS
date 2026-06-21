"""Market asking price inquiry DTOs."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class InquireAskingPriceRequestDto(BaseModel):
    """Request DTO for domestic stock asking price inquiry."""

    fid_cond_mrkt_div_code: str = "J"
    fid_input_iscd: str

    def to_params(self) -> dict[str, str]:
        """Convert to KIS REST query parameters."""
        return {
            "FID_COND_MRKT_DIV_CODE": self.fid_cond_mrkt_div_code,
            "FID_INPUT_ISCD": self.fid_input_iscd,
        }


class InquireAskingPriceResponseDto(BaseModel):
    """Response DTO for domestic stock asking price inquiry."""

    stock_code: str = ""
    stock_name: str = ""
    bid_prices: list[str] = Field(default_factory=list)
    ask_prices: list[str] = Field(default_factory=list)
    bid_quantities: list[str] = Field(default_factory=list)
    ask_quantities: list[str] = Field(default_factory=list)

    @classmethod
    def from_api_output(cls, output: dict[str, Any]) -> InquireAskingPriceResponseDto:
        """Build DTO from KIS ``output`` section."""
        bid_prices = [_field(output, f"bidp{index}") for index in range(1, 11)]
        ask_prices = [_field(output, f"askp{index}") for index in range(1, 11)]
        bid_quantities = [_field(output, f"bidp_rsqn{index}") for index in range(1, 11)]
        ask_quantities = [_field(output, f"askp_rsqn{index}") for index in range(1, 11)]
        return cls(
            stock_code=str(output.get("mksc_shrn_iscd", output.get("stck_shrn_iscd", ""))),
            stock_name=str(output.get("hts_kor_isnm", "")),
            bid_prices=[price for price in bid_prices if price],
            ask_prices=[price for price in ask_prices if price],
            bid_quantities=[qty for qty in bid_quantities if qty],
            ask_quantities=[qty for qty in ask_quantities if qty],
        )


def _field(output: dict[str, Any], key: str) -> str:
    value = output.get(key)
    if value is None:
        return ""
    return str(value)
