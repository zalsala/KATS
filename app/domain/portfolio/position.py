"""Position domain model."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


def _to_decimal(value: str | Decimal | int | float) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value).replace(",", ""))


@dataclass(slots=True)
class Position:
    """Single stock position in a portfolio."""

    symbol_code: str
    stock_name: str
    quantity: Decimal
    average_price: Decimal
    current_price: Decimal

    @property
    def purchase_amount(self) -> Decimal:
        """Return total purchase amount."""
        return self.quantity * self.average_price

    @property
    def evaluation_amount(self) -> Decimal:
        """Return market evaluation amount."""
        return self.quantity * self.current_price

    @property
    def profit_loss_amount(self) -> Decimal:
        """Return unrealized profit or loss."""
        return self.evaluation_amount - self.purchase_amount

    @property
    def profit_loss_rate(self) -> Decimal:
        """Return profit/loss rate in percent."""
        if self.purchase_amount == 0:
            return Decimal("0")
        return (self.profit_loss_amount / self.purchase_amount) * Decimal("100")

    def with_price(self, current_price: Decimal) -> Position:
        """Return a copy with updated current price."""
        return Position(
            symbol_code=self.symbol_code,
            stock_name=self.stock_name,
            quantity=self.quantity,
            average_price=self.average_price,
            current_price=current_price,
        )

    def apply_buy(self, quantity: Decimal, price: Decimal) -> Position:
        """Apply a buy fill and return updated average price."""
        if quantity <= 0:
            return self
        total_cost = (self.quantity * self.average_price) + (quantity * price)
        new_qty = self.quantity + quantity
        new_avg = total_cost / new_qty if new_qty > 0 else Decimal("0")
        return Position(
            symbol_code=self.symbol_code,
            stock_name=self.stock_name,
            quantity=new_qty,
            average_price=new_avg,
            current_price=price,
        )

    def apply_sell(self, quantity: Decimal) -> Position | None:
        """Apply a sell fill. Returns None when position is closed."""
        if quantity <= 0:
            return self
        new_qty = self.quantity - quantity
        if new_qty <= 0:
            return None
        return Position(
            symbol_code=self.symbol_code,
            stock_name=self.stock_name,
            quantity=new_qty,
            average_price=self.average_price,
            current_price=self.current_price,
        )

    @classmethod
    def from_payload(cls, payload: dict[str, str]) -> Position:
        """Build a position from event payload fields."""
        return cls(
            symbol_code=str(payload.get("symbol_code", "")),
            stock_name=str(payload.get("stock_name", "")),
            quantity=_to_decimal(payload.get("quantity", "0")),
            average_price=_to_decimal(payload.get("average_price", "0")),
            current_price=_to_decimal(
                payload.get("current_price", payload.get("average_price", "0"))
            ),
        )
