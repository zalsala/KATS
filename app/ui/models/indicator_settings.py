"""Indicator overlay configuration for the chart UI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(slots=True)
class IndicatorSettings:
    """User-configurable indicator overlay parameters."""

    sma_enabled: bool = True
    sma_period: int = 20
    ema_enabled: bool = False
    ema_period: int = 20
    vwap_enabled: bool = False

    MIN_PERIOD: ClassVar[int] = 1
    MAX_PERIOD: ClassVar[int] = 500

    def validate(self) -> None:
        """Raise ``ValueError`` when a period is outside the allowed range."""
        if not self.MIN_PERIOD <= self.sma_period <= self.MAX_PERIOD:
            raise ValueError(f"SMA period must be between {self.MIN_PERIOD} and {self.MAX_PERIOD}")
        if not self.MIN_PERIOD <= self.ema_period <= self.MAX_PERIOD:
            raise ValueError(f"EMA period must be between {self.MIN_PERIOD} and {self.MAX_PERIOD}")

    @classmethod
    def clamp_period(cls, value: int) -> int:
        """Clamp a period value to the supported UI range."""
        return max(cls.MIN_PERIOD, min(cls.MAX_PERIOD, value))
