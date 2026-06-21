"""Technical indicator helpers."""

from __future__ import annotations

from decimal import Decimal


def compute_sma(prices: list[Decimal], period: int) -> Decimal | None:
    """Compute simple moving average for the latest window."""
    if period <= 0 or len(prices) < period:
        return None
    window = prices[-period:]
    return sum(window, Decimal("0")) / Decimal(period)


def compute_rsi(prices: list[Decimal], period: int) -> Decimal | None:
    """Compute RSI for the latest price series."""
    if period <= 0 or len(prices) <= period:
        return None

    gains: list[Decimal] = []
    losses: list[Decimal] = []
    for index in range(1, len(prices)):
        change = prices[index] - prices[index - 1]
        if change >= 0:
            gains.append(change)
            losses.append(Decimal("0"))
        else:
            gains.append(Decimal("0"))
            losses.append(abs(change))

    if len(gains) < period:
        return None

    avg_gain = sum(gains[-period:], Decimal("0")) / Decimal(period)
    avg_loss = sum(losses[-period:], Decimal("0")) / Decimal(period)
    if avg_loss == 0:
        return Decimal("100")
    rs = avg_gain / avg_loss
    return Decimal("100") - (Decimal("100") / (Decimal("1") + rs))
