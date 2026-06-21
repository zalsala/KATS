"""Moving average cross strategy plugin."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from app.domain.strategy.trading_signal import SignalType, TradingSignal
from app.strategy.base_strategy import BaseStrategy
from app.strategy.indicators import compute_sma
from app.strategy.strategy_context import StrategyContext


def _to_decimal(value: str | Decimal | int | float) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value).replace(",", ""))


class MovingAverageCrossStrategy(BaseStrategy):
    """Generate signals on short/long SMA crossover."""

    strategy_type = "moving_average_cross"

    def initialize(self, context: StrategyContext) -> None:
        context.custom_state.setdefault("prices", {})

    def on_start(self, context: StrategyContext) -> None:
        context.custom_state["started"] = True

    def on_market_data(
        self,
        context: StrategyContext,
        payload: dict[str, Any],
    ) -> TradingSignal | None:
        symbol_code = str(payload.get("symbol_code", payload.get("symbol", "")))
        if symbol_code not in context.symbols:
            return None

        price = _to_decimal(payload.get("price", payload.get("current_price", "0")))
        prices_map: dict[str, list[Decimal]] = context.custom_state.setdefault("prices", {})
        history = prices_map.setdefault(symbol_code, [])
        history.append(price)

        short_period = int(context.parameters.get("short_period", 3))
        long_period = int(context.parameters.get("long_period", 5))
        if len(history) < long_period + 1:
            return None

        prev_short = compute_sma(history[:-1], short_period)
        prev_long = compute_sma(history[:-1], long_period)
        curr_short = compute_sma(history, short_period)
        curr_long = compute_sma(history, long_period)
        if None in {prev_short, prev_long, curr_short, curr_long}:
            return None

        assert prev_short is not None
        assert prev_long is not None
        assert curr_short is not None
        assert curr_long is not None

        quantity = _to_decimal(context.parameters.get("quantity", "1"))
        if prev_short <= prev_long and curr_short > curr_long:
            return TradingSignal(
                signal_id="",
                strategy_id=context.strategy_id,
                strategy_name=context.strategy_name,
                symbol_code=symbol_code,
                signal_type=SignalType.BUY,
                price=price,
                quantity=quantity,
                confidence=Decimal("0.8"),
                timestamp=datetime.now(UTC),
                reason="ma_golden_cross",
            )

        if prev_short >= prev_long and curr_short < curr_long:
            return TradingSignal(
                signal_id="",
                strategy_id=context.strategy_id,
                strategy_name=context.strategy_name,
                symbol_code=symbol_code,
                signal_type=SignalType.SELL,
                price=price,
                quantity=quantity,
                confidence=Decimal("0.8"),
                timestamp=datetime.now(UTC),
                reason="ma_death_cross",
            )

        return None

    def on_stop(self, context: StrategyContext) -> None:
        context.custom_state["stopped"] = True
