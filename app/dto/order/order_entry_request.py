"""Order entry request DTO."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.dto.order.order_constants import ORDER_DIVISION_LIMIT, ORDER_DIVISION_MARKET

OrderSide = Literal["buy", "sell"]
OrderType = Literal["limit", "market"]


@dataclass(frozen=True, slots=True)
class OrderEntryRequest:
    """Validated order entry payload for domestic cash orders."""

    symbol_code: str
    side: OrderSide
    order_type: OrderType
    quantity: str
    price: str

    @property
    def order_division(self) -> str:
        """Return the KIS ``ORD_DVSN`` value for this order."""
        if self.order_type == "market":
            return ORDER_DIVISION_MARKET
        return ORDER_DIVISION_LIMIT

    @property
    def is_market_order(self) -> bool:
        """Return True when this is a market order."""
        return self.order_type == "market"
