"""Portfolio aggregate."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal

from app.domain.portfolio.cash_balance import CashBalance
from app.domain.portfolio.position import Position


@dataclass(slots=True)
class Portfolio:
    """Current portfolio state."""

    account_no: str
    cash: CashBalance = field(default_factory=CashBalance.zero)
    positions: dict[str, Position] = field(default_factory=dict)
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def total_evaluation(self) -> Decimal:
        """Return total stock evaluation amount."""
        return sum((pos.evaluation_amount for pos in self.positions.values()), Decimal("0"))

    @property
    def total_purchase(self) -> Decimal:
        """Return total purchase amount of held stocks."""
        return sum((pos.purchase_amount for pos in self.positions.values()), Decimal("0"))

    @property
    def total_profit_loss(self) -> Decimal:
        """Return total unrealized profit or loss."""
        return self.total_evaluation - self.total_purchase

    @property
    def total_asset(self) -> Decimal:
        """Return total asset including cash."""
        return self.cash.total_deposit + self.total_evaluation

    @property
    def profit_rate(self) -> Decimal:
        """Return portfolio profit rate in percent."""
        if self.total_purchase == 0:
            return Decimal("0")
        return (self.total_profit_loss / self.total_purchase) * Decimal("100")

    def touch(self) -> None:
        """Update the last modified timestamp."""
        self.updated_at = datetime.now(UTC)
