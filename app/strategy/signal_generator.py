"""Trading signal generator."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

from app.domain.strategy.trading_signal import SignalType, TradingSignal


def _to_decimal(value: str | Decimal | int | float) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value).replace(",", ""))


class SignalGenerator:
    """Builds normalized ``TradingSignal`` objects."""

    def create(
        self,
        *,
        strategy_id: str,
        strategy_name: str,
        symbol_code: str,
        signal_type: SignalType,
        price: Decimal,
        quantity: Decimal,
        confidence: Decimal = Decimal("1"),
        reason: str = "",
        timestamp: datetime | None = None,
    ) -> TradingSignal:
        """Create a trading signal with generated ID and timestamp."""
        return TradingSignal(
            signal_id=str(uuid4()),
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            symbol_code=symbol_code,
            signal_type=signal_type,
            price=price,
            quantity=quantity,
            confidence=confidence,
            timestamp=timestamp or datetime.now(UTC),
            reason=reason,
        )

    def from_strategy_output(
        self,
        *,
        strategy_id: str,
        strategy_name: str,
        output: TradingSignal,
    ) -> TradingSignal:
        """Normalize a strategy-produced signal."""
        return self.create(
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            symbol_code=output.symbol_code,
            signal_type=output.signal_type,
            price=output.price,
            quantity=output.quantity,
            confidence=output.confidence,
            reason=output.reason,
            timestamp=output.timestamp,
        )

    def from_payload(
        self,
        *,
        strategy_id: str,
        strategy_name: str,
        payload: dict[str, Any],
    ) -> TradingSignal | None:
        """Build a signal from a loose payload dict."""
        signal_type_raw = str(payload.get("signal_type", "")).upper()
        if signal_type_raw not in SignalType.__members__:
            return None
        symbol_code = str(payload.get("symbol_code", payload.get("symbol", "")))
        if not symbol_code:
            return None
        return self.create(
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            symbol_code=symbol_code,
            signal_type=SignalType(signal_type_raw),
            price=_to_decimal(payload.get("price", "0")),
            quantity=_to_decimal(payload.get("quantity", "0")),
            confidence=_to_decimal(payload.get("confidence", "1")),
            reason=str(payload.get("reason", "")),
        )
