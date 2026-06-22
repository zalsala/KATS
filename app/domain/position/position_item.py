"""Normalized domestic stock position for the UI."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.domain.account.entities.holding_stock import HoldingStock


@dataclass(frozen=True, slots=True)
class PositionItem:
    """Single domestic stock holding row for the position panel."""

    symbol_code: str
    stock_name: str
    quantity: Decimal
    average_price: Decimal
    current_price: Decimal
    evaluation_amount: Decimal
    profit_loss_amount: Decimal
    profit_loss_rate: Decimal

    @classmethod
    def from_holding_stock(cls, holding: HoldingStock) -> PositionItem:
        """Build a position item from a KIS holding entity."""
        return cls(
            symbol_code=holding.symbol_code,
            stock_name=holding.stock_name,
            quantity=holding.quantity,
            average_price=holding.average_price,
            current_price=holding.current_price,
            evaluation_amount=holding.evaluation_amount,
            profit_loss_amount=holding.profit_loss_amount,
            profit_loss_rate=holding.profit_loss_rate,
        )

    def with_current_price(self, current_price: Decimal) -> PositionItem:
        """Return a copy with updated market price and derived valuation fields."""
        evaluation_amount = self.quantity * current_price
        cost_basis = self.quantity * self.average_price
        profit_loss_amount = evaluation_amount - cost_basis
        if cost_basis > 0:
            profit_loss_rate = (profit_loss_amount / cost_basis) * Decimal("100")
        else:
            profit_loss_rate = Decimal("0")
        return PositionItem(
            symbol_code=self.symbol_code,
            stock_name=self.stock_name,
            quantity=self.quantity,
            average_price=self.average_price,
            current_price=current_price,
            evaluation_amount=evaluation_amount,
            profit_loss_amount=profit_loss_amount,
            profit_loss_rate=profit_loss_rate,
        )
