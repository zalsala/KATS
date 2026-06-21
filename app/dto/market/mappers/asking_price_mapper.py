"""Asking price DTO to entity mapper."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from app.domain.market.entities.asking_price import AskingPrice, PriceLevel
from app.domain.market.value_objects.symbol import Symbol
from app.dto.market.inquire_asking_price_dto import InquireAskingPriceResponseDto


class AskingPriceMapper:
    """Maps asking price DTOs to domain entities."""

    @staticmethod
    def to_entity(
        dto: InquireAskingPriceResponseDto,
        *,
        symbol: Symbol,
        queried_at: datetime | None = None,
    ) -> AskingPrice:
        """Convert an asking price response DTO into an ``AskingPrice`` entity."""
        bid_levels = _build_levels(dto.bid_prices, dto.bid_quantities)
        ask_levels = _build_levels(dto.ask_prices, dto.ask_quantities)
        return AskingPrice(
            symbol=symbol,
            stock_name=dto.stock_name,
            bid_levels=bid_levels,
            ask_levels=ask_levels,
            queried_at=queried_at or datetime.now(UTC),
        )


def _build_levels(prices: list[str], quantities: list[str]) -> tuple[PriceLevel, ...]:
    levels: list[PriceLevel] = []
    for index, price in enumerate(prices, start=1):
        quantity = quantities[index - 1] if index - 1 < len(quantities) else "0"
        if not price:
            continue
        levels.append(
            PriceLevel(
                price=_to_decimal(price),
                quantity=_to_decimal(quantity),
                level=index,
            )
        )
    return tuple(levels)


def _to_decimal(value: str) -> Decimal:
    if not value:
        return Decimal("0")
    return Decimal(value.replace(",", ""))
