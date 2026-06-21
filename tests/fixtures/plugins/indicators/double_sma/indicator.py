"""Double SMA indicator plugin for tests."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.plugins.base_indicator import BaseIndicator


class DoubleSmaIndicator(BaseIndicator):
    """Return SMA multiplied by two."""

    indicator_name = "double_sma"

    def compute(self, prices: list[Decimal], **parameters: Any) -> Decimal | None:
        period = int(parameters.get("period", 3))
        if period <= 0 or len(prices) < period:
            return None
        window = prices[-period:]
        sma = sum(window, Decimal("0")) / Decimal(period)
        return sma * Decimal("2")
