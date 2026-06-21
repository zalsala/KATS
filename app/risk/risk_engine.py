"""Risk validation engine."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from app.domain.portfolio.portfolio_snapshot import PortfolioSnapshot
from app.domain.risk.risk_policy import RiskPolicy
from app.domain.risk.risk_result import RiskResult
from app.domain.strategy.trading_signal import SignalType, TradingSignal
from app.events.domain_events import RiskEvent
from app.events.event_bus_service import EventBusService
from app.risk.risk_evaluator import RiskEvaluator
from app.risk.risk_manager import RiskManager
from app.service.portfolio.portfolio_service import PortfolioService


def _resolve_logger() -> logging.Logger:
    return logging.getLogger(__name__)


def _to_decimal(value: str | Decimal | int | float) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value).replace(",", ""))


class RiskEngine:
    """Validates strategy signals against portfolio state and risk policy."""

    def __init__(
        self,
        *,
        portfolio_service: PortfolioService,
        manager: RiskManager,
        evaluator: RiskEvaluator | None = None,
        policy: RiskPolicy | None = None,
        event_bus: EventBusService | None = None,
        source: str = "risk_engine",
    ) -> None:
        self._portfolio_service = portfolio_service
        self._manager = manager
        self._evaluator = evaluator or RiskEvaluator()
        self._policy = policy or RiskPolicy.default()
        self._event_bus = event_bus
        self._source = source
        self._logger = _resolve_logger()

    @property
    def manager(self) -> RiskManager:
        return self._manager

    @property
    def policy(self) -> RiskPolicy:
        return self._policy

    def set_policy(self, policy: RiskPolicy) -> None:
        """Replace active risk policy."""
        self._policy = policy
        self._manager.set_emergency_stop(policy.emergency_stop)

    def handle_strategy_signal(self, payload: dict[str, Any]) -> RiskResult:
        """Validate a strategy signal payload and publish a risk event."""
        signal = self._extract_signal(payload)
        if signal is None:
            result = RiskResult(
                approved=False,
                signal_id=str(payload.get("signal_id", "")),
                symbol_code=str(payload.get("symbol_code", "")),
                signal_type=str(payload.get("signal_type", "")),
                violations=(),
                message="invalid_signal_payload",
            )
            self._publish_risk_event(result, signal=None)
            return result

        portfolio = self._portfolio_service.get_snapshot()
        result = self._evaluator.evaluate(
            signal,
            portfolio=portfolio,
            policy=self._policy,
            manager=self._manager,
        )

        if result.approved and signal.signal_type in {SignalType.BUY, SignalType.SELL}:
            self._manager.register_pending_order(signal.symbol_code)

        self._publish_risk_event(result, signal=signal)
        return result

    def handle_execution(self, payload: dict[str, Any]) -> None:
        """Clear pending order state when an execution is received."""
        symbol_code = str(payload.get("symbol_code", payload.get("symbol", "")))
        if symbol_code:
            self._manager.clear_pending_order(symbol_code)

    def validate_signal(
        self,
        signal: TradingSignal,
        *,
        portfolio: PortfolioSnapshot | None = None,
    ) -> RiskResult:
        """Validate a signal directly without EventBus."""
        snapshot = portfolio or self._portfolio_service.get_snapshot()
        result = self._evaluator.evaluate(
            signal,
            portfolio=snapshot,
            policy=self._policy,
            manager=self._manager,
        )
        if result.approved and signal.signal_type in {SignalType.BUY, SignalType.SELL}:
            self._manager.register_pending_order(signal.symbol_code)
        self._publish_risk_event(result, signal=signal)
        return result

    def _extract_signal(self, payload: dict[str, Any]) -> TradingSignal | None:
        signal_type_raw = str(payload.get("signal_type", "")).upper()
        if signal_type_raw not in SignalType.__members__:
            return None
        symbol_code = str(payload.get("symbol_code", payload.get("symbol", "")))
        if not symbol_code:
            return None
        signal_id = str(payload.get("signal_id", ""))
        if not signal_id:
            return None

        timestamp_raw = payload.get("timestamp")
        if isinstance(timestamp_raw, str) and timestamp_raw:
            timestamp = datetime.fromisoformat(timestamp_raw)
        else:
            timestamp = datetime.now(UTC)

        return TradingSignal(
            signal_id=signal_id,
            strategy_id=str(payload.get("strategy_id", "")),
            strategy_name=str(payload.get("strategy_name", "")),
            symbol_code=symbol_code,
            signal_type=SignalType(signal_type_raw),
            price=_to_decimal(payload.get("price", "0")),
            quantity=_to_decimal(payload.get("quantity", "0")),
            confidence=_to_decimal(payload.get("confidence", "1")),
            timestamp=timestamp,
            reason=str(payload.get("message", payload.get("reason", ""))),
        )

    def _publish_risk_event(
        self,
        result: RiskResult,
        *,
        signal: TradingSignal | None,
    ) -> None:
        self._logger.info(
            "Risk validation status=%s signal_id=%s symbol=%s violations=%s",
            result.status,
            result.signal_id,
            result.symbol_code,
            len(result.violations),
        )
        if self._event_bus is None:
            return

        self._event_bus.publish(
            RiskEvent(
                source=self._source,
                event_name="risk.validated",
                payload={
                    "status": result.status,
                    "approved": result.approved,
                    "signal_id": result.signal_id,
                    "symbol_code": result.symbol_code,
                    "signal_type": result.signal_type,
                    "strategy_id": signal.strategy_id if signal else "",
                    "strategy_name": signal.strategy_name if signal else "",
                    "price": str(signal.price) if signal else "",
                    "quantity": str(signal.quantity) if signal else "",
                    "message": result.message,
                    "violations": [
                        {"rule_code": item.rule_code, "message": item.message}
                        for item in result.violations
                    ],
                },
                correlation_id=result.signal_id,
            )
        )
