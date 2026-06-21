"""Cash balance domain model."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(slots=True)
class CashBalance:
    """Cash balance within a portfolio."""

    total_deposit: Decimal
    orderable_cash: Decimal

    @classmethod
    def zero(cls) -> CashBalance:
        """Return an empty cash balance."""
        return cls(total_deposit=Decimal("0"), orderable_cash=Decimal("0"))
