"""Signal evaluation result."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.strategy.trading_signal import TradingSignal


@dataclass(frozen=True, slots=True)
class SignalResult:
    """Result of signal generation and evaluation."""

    signal: TradingSignal | None
    evaluated: bool
    accepted: bool
    message: str = ""
