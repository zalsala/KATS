"""Trading signal evaluator."""

from __future__ import annotations

from decimal import Decimal

from app.domain.strategy.signal_result import SignalResult
from app.domain.strategy.trading_signal import SignalType, TradingSignal
from app.strategy.strategy_context import StrategyContext


class SignalEvaluator:
    """Validates and filters generated trading signals."""

    def evaluate(
        self,
        signal: TradingSignal | None,
        *,
        context: StrategyContext,
    ) -> SignalResult:
        """Evaluate whether a signal should be published."""
        if signal is None:
            return SignalResult(signal=None, evaluated=False, accepted=False, message="no_signal")

        if signal.symbol_code not in context.symbols:
            return SignalResult(
                signal=signal,
                evaluated=True,
                accepted=False,
                message="symbol_not_subscribed",
            )

        if signal.price <= Decimal("0") and signal.signal_type in {SignalType.BUY, SignalType.SELL}:
            return SignalResult(
                signal=signal,
                evaluated=True,
                accepted=False,
                message="invalid_price",
            )

        if signal.quantity <= Decimal("0") and signal.signal_type in {
            SignalType.BUY,
            SignalType.SELL,
        }:
            return SignalResult(
                signal=signal,
                evaluated=True,
                accepted=False,
                message="invalid_quantity",
            )

        return SignalResult(
            signal=signal,
            evaluated=True,
            accepted=True,
            message="accepted",
        )
