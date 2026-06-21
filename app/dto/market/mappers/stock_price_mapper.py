"""Stock price DTO to entity mapper."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from app.domain.market.entities.stock_price import StockPrice
from app.domain.market.value_objects.symbol import Symbol
from app.dto.market.inquire_price_dto import InquirePriceResponseDto


class StockPriceMapper:
    """Maps market price DTOs to domain entities."""

    @staticmethod
    def to_entity(
        dto: InquirePriceResponseDto,
        *,
        symbol: Symbol,
        queried_at: datetime | None = None,
    ) -> StockPrice:
        """Convert a price response DTO into a ``StockPrice`` entity.

        Args:
            dto: Parsed price response DTO.
            symbol: Requested stock symbol.
            queried_at: Optional query timestamp.

        Returns:
            Domain stock price entity.
        """
        return StockPrice(
            symbol=symbol,
            stock_name=dto.stock_name,
            current_price=_to_decimal(dto.current_price),
            change_amount=_to_decimal(dto.change_amount),
            change_rate=_to_decimal(dto.change_rate),
            queried_at=queried_at or datetime.now(UTC),
        )


def _to_decimal(value: str) -> Decimal:
    if not value:
        return Decimal("0")
    return Decimal(value.replace(",", ""))
