"""Supported candle timeframes."""

from __future__ import annotations

from enum import Enum


class Timeframe(Enum):
    """Candle aggregation intervals."""

    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    H1 = "60m"


SUPPORTED_TIMEFRAMES: tuple[Timeframe, ...] = (
    Timeframe.M1,
    Timeframe.M5,
    Timeframe.M15,
    Timeframe.H1,
)

DEFAULT_TIMEFRAME = Timeframe.M1


def resolve_timeframe(timeframe: Timeframe | str) -> Timeframe:
    """Return a Timeframe enum from a value or enum member."""
    if isinstance(timeframe, Timeframe):
        return timeframe
    return Timeframe(timeframe)
