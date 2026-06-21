"""Example external strategy plugin."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from app.domain.strategy.trading_signal import SignalType, TradingSignal
from app.strategy.base_strategy import BaseStrategy
from app.strategy.strategy_context import StrategyContext


class ExampleHoldOnceStrategy(BaseStrategy):
    """Example buy-once strategy for the plugins/ folder."""

    strategy_type = "example_hold_once"

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

        price = Decimal(str(payload.get("price", payload.get("current_price", "0"))))
        buy_qty = Decimal(str(context.parameters.get("quantity", "1")))
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
            reason="example_hold_once_entry",
        )

    def on_stop(self, context: StrategyContext) -> None:
        context.custom_state["stopped"] = True
