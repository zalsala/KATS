"""Buy and hold strategy plugin."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from app.domain.strategy.trading_signal import SignalType, TradingSignal
from app.strategy.base_strategy import BaseStrategy
from app.strategy.strategy_context import StrategyContext


def _to_decimal(value: str | Decimal | int | float) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value).replace(",", ""))


class BuyAndHoldStrategy(BaseStrategy):
    """Buy once when flat, then hold."""

    strategy_type = "buy_and_hold"

    def initialize(self, context: StrategyContext) -> None:
        context.custom_state.setdefault("initialized", True)

    def on_start(self, context: StrategyContext) -> None:
        context.custom_state["started"] = True

    def on_market_data(
        self,
        context: StrategyContext,
        payload: dict[str, Any],
    ) -> TradingSignal | None:
        if context.custom_state.get("bought"):
            return None

        symbol_code = str(payload.get("symbol_code", payload.get("symbol", "")))
        if symbol_code not in context.symbols:
            return None

        quantity = context.get_position_quantity(symbol_code)
        if quantity > 0:
            context.custom_state["bought"] = True
            return None

        price = _to_decimal(payload.get("price", payload.get("current_price", "0")))
        buy_qty = _to_decimal(context.parameters.get("quantity", "1"))
        context.custom_state["bought"] = True
        return TradingSignal(
            signal_id="",
            strategy_id=context.strategy_id,
            strategy_name=context.strategy_name,
            symbol_code=symbol_code,
            signal_type=SignalType.BUY,
            price=price,
            quantity=buy_qty,
            confidence=Decimal("1"),
            timestamp=datetime.now(UTC),
            reason="buy_and_hold_entry",
        )

    def on_stop(self, context: StrategyContext) -> None:
        context.custom_state["stopped"] = True
