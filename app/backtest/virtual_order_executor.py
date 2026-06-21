"""Virtual order executor for backtests."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

from app.backtest.backtest_portfolio import BacktestPortfolio
from app.backtest.performance_analyzer import PerformanceAnalyzer
from app.domain.strategy.trading_signal import SignalType
from app.events.base_event import BaseEvent
from app.events.domain_events import ExecutionEvent
from app.events.event_bus_service import EventBusService
from app.events.event_types import EventType
from app.portfolio.portfolio_engine import BUY_SIDE, SELL_SIDE


class VirtualOrderExecutor:
    """Executes approved risk signals as virtual orders."""

    def __init__(
        self,
        *,
        portfolio: BacktestPortfolio,
        analyzer: PerformanceAnalyzer,
        event_bus: EventBusService | None = None,
        source: str = "virtual_order_executor",
    ) -> None:
        self._portfolio = portfolio
        self._analyzer = analyzer
        self._event_bus = event_bus
        self._source = source
        self._logger = logging.getLogger(__name__)
        self._subscription_ids: list[str] = []

    @property
    def subscription_ids(self) -> tuple[str, ...]:
        """Return active EventBus subscription IDs."""
        return tuple(self._subscription_ids)

    def register(self, event_bus: EventBusService) -> tuple[str, ...]:
        """Subscribe to approved risk events."""
        self._subscription_ids = [
            event_bus.subscribe(EventType.RISK, self.handle_risk_event),
        ]
        return tuple(self._subscription_ids)

    def unregister(self, event_bus: EventBusService) -> None:
        """Unsubscribe virtual order handler."""
        for subscription_id in self._subscription_ids:
            event_bus.unsubscribe(subscription_id)
        self._subscription_ids.clear()

    def handle_risk_event(self, event: BaseEvent) -> None:
        """Process approved risk events as virtual orders."""
        payload = event.payload
        if payload.get("status") != "APPROVED" or not payload.get("approved"):
            return

        signal_type = str(payload.get("signal_type", "")).upper()
        if signal_type not in {SignalType.BUY.value, SignalType.SELL.value}:
            return

        symbol_code = str(payload.get("symbol_code", ""))
        price = Decimal(str(payload.get("price", "0")))
        quantity = Decimal(str(payload.get("quantity", "0")))
        if not symbol_code or price <= 0 or quantity <= 0:
            return

        side = BUY_SIDE if signal_type == SignalType.BUY.value else SELL_SIDE
        timestamp_raw = payload.get("timestamp")
        if isinstance(timestamp_raw, str) and timestamp_raw:
            timestamp = datetime.fromisoformat(timestamp_raw)
        else:
            timestamp = datetime.now(UTC)

        avg_price = self._resolve_average_price(symbol_code)
        execution_payload = {
            "symbol_code": symbol_code,
            "side": side,
            "executed_quantity": str(quantity),
            "executed_price": str(price),
            "stock_name": symbol_code,
            "timestamp": timestamp.isoformat(),
        }

        snapshot = self._portfolio.apply_virtual_fill(execution_payload)
        _ = snapshot
        realized_pnl = Decimal("0")
        if signal_type == SignalType.SELL.value and avg_price is not None:
            realized_pnl = (price - avg_price) * quantity

        self._analyzer.record_trade(
            symbol_code=symbol_code,
            side=side,
            quantity=quantity,
            price=price,
            timestamp=timestamp,
            realized_pnl=realized_pnl,
        )

        if self._event_bus is not None:
            self._event_bus.publish(
                ExecutionEvent(
                    source=self._source,
                    payload=execution_payload,
                    correlation_id=str(payload.get("signal_id", uuid4())),
                )
            )

        self._logger.info(
            "Virtual order filled symbol=%s side=%s qty=%s price=%s",
            symbol_code,
            side,
            quantity,
            price,
        )

    def execute_approved_payload(self, payload: dict[str, Any]) -> None:
        """Execute a virtual order from an approved risk payload directly."""
        from app.events.domain_events import RiskEvent

        self.handle_risk_event(
            RiskEvent(source=self._source, payload=payload),
        )

    def _resolve_average_price(self, symbol_code: str) -> Decimal | None:
        snapshot = self._portfolio.get_snapshot()
        for position in snapshot.positions:
            if position.symbol_code == symbol_code:
                return position.average_price
        return None
