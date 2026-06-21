"""RSI strategy plugin."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from app.domain.strategy.trading_signal import SignalType, TradingSignal
from app.strategy.base_strategy import BaseStrategy
from app.strategy.indicators import compute_rsi
from app.strategy.strategy_context import StrategyContext


def _to_decimal(value: str | Decimal | int | float) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value).replace(",", ""))


class RSIStrategy(BaseStrategy):
    """Buy on oversold RSI and sell on overbought RSI."""

    strategy_type = "rsi"

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

        period = int(context.parameters.get("period", 14))
        buy_threshold = _to_decimal(context.parameters.get("buy_threshold", "30"))
        sell_threshold = _to_decimal(context.parameters.get("sell_threshold", "70"))
        quantity = _to_decimal(context.parameters.get("quantity", "1"))

        rsi = compute_rsi(history, period)
        if rsi is None:
            return None

        if rsi <= buy_threshold:
            return TradingSignal(
                signal_id="",
                strategy_id=context.strategy_id,
                strategy_name=context.strategy_name,
                symbol_code=symbol_code,
                signal_type=SignalType.BUY,
                price=price,
                quantity=quantity,
                confidence=Decimal("0.7"),
                timestamp=datetime.now(UTC),
                reason=f"rsi_oversold_{rsi}",
            )

        if rsi >= sell_threshold:
            return TradingSignal(
                signal_id="",
                strategy_id=context.strategy_id,
                strategy_name=context.strategy_name,
                symbol_code=symbol_code,
                signal_type=SignalType.SELL,
                price=price,
                quantity=quantity,
                confidence=Decimal("0.7"),
                timestamp=datetime.now(UTC),
                reason=f"rsi_overbought_{rsi}",
            )

        return TradingSignal(
            signal_id="",
            strategy_id=context.strategy_id,
            strategy_name=context.strategy_name,
            symbol_code=symbol_code,
            signal_type=SignalType.HOLD,
            price=price,
            quantity=Decimal("0"),
            confidence=Decimal("0.5"),
            timestamp=datetime.now(UTC),
            reason=f"rsi_neutral_{rsi}",
        )

    def on_stop(self, context: StrategyContext) -> None:
        context.custom_state["stopped"] = True
