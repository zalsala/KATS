"""Strategy orchestration engine."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from app.domain.portfolio.portfolio_snapshot import PortfolioSnapshot
from app.domain.strategy.signal_result import SignalResult
from app.domain.strategy.strategy_state import StrategyState
from app.domain.strategy.trading_signal import TradingSignal
from app.events.domain_events import StrategyEvent
from app.events.event_bus_service import EventBusService
from app.strategy.signal_evaluator import SignalEvaluator
from app.strategy.signal_generator import SignalGenerator
from app.strategy.strategy_executor import StrategyExecutor
from app.strategy.strategy_manager import ManagedStrategy, StrategyManager


def _resolve_logger() -> logging.Logger:
    return logging.getLogger(__name__)


def _extract_symbol(payload: dict[str, Any]) -> str:
    return str(payload.get("symbol_code", payload.get("symbol", "")))


def _extract_price(payload: dict[str, Any]) -> Decimal:
    raw = payload.get("price", payload.get("current_price", "0"))
    return Decimal(str(raw).replace(",", ""))


class StrategyEngine:
    """Coordinates strategy execution and signal publication."""

    def __init__(
        self,
        *,
        manager: StrategyManager,
        executor: StrategyExecutor | None = None,
        signal_generator: SignalGenerator | None = None,
        signal_evaluator: SignalEvaluator | None = None,
        event_bus: EventBusService | None = None,
        source: str = "strategy_engine",
    ) -> None:
        self._manager = manager
        self._executor = executor or StrategyExecutor()
        self._generator = signal_generator or SignalGenerator()
        self._evaluator = signal_evaluator or SignalEvaluator()
        self._event_bus = event_bus
        self._source = source
        self._logger = _resolve_logger()
        self._portfolio_snapshot: PortfolioSnapshot | None = None

    def set_portfolio_snapshot(self, snapshot: PortfolioSnapshot | None) -> None:
        """Update portfolio snapshot for all strategies."""
        self._portfolio_snapshot = snapshot
        if snapshot is None:
            return
        for managed in self._manager.list_managed():
            self._manager.update_portfolio_snapshot(managed.entity.strategy_id, snapshot)

    def handle_market_data(self, payload: dict[str, Any]) -> list[SignalResult]:
        """Process market data for all subscribed running strategies."""
        symbol_code = _extract_symbol(payload)
        if not symbol_code:
            return []
        price = _extract_price(payload)
        self._manager.update_price(symbol_code, price)

        results: list[SignalResult] = []
        for managed in self._manager.get_running_for_symbol(symbol_code):
            self._manager.record_market_data(managed.entity.strategy_id)
            raw_signal = self._executor.execute_market_data(
                managed.instance,
                managed.context,
                payload,
            )
            result = self._process_signal(
                raw_signal,
                managed=managed,
                event_name="strategy.signal.generated",
                reason="market_data",
            )
            if result is not None:
                results.append(result)
        return results

    def handle_execution(self, payload: dict[str, Any]) -> list[SignalResult]:
        """Process execution events for running strategies."""
        symbol_code = _extract_symbol(payload)
        results: list[SignalResult] = []
        targets = (
            self._manager.get_running_for_symbol(symbol_code)
            if symbol_code
            else [
                managed
                for managed in self._manager.list_managed()
                if managed.entity.state == StrategyState.RUNNING
            ]
        )
        for managed in targets:
            self._manager.record_execution(managed.entity.strategy_id)
            raw_signal = self._executor.execute_execution(
                managed.instance,
                managed.context,
                payload,
            )
            result = self._process_signal(
                raw_signal,
                managed=managed,
                event_name="strategy.execution.processed",
                reason="execution",
            )
            if result is not None:
                results.append(result)
        return results

    def handle_portfolio_changed(self, payload: dict[str, Any]) -> list[SignalResult]:
        """Process portfolio update events."""
        results: list[SignalResult] = []
        for managed in self._manager.list_managed():
            if managed.entity.state != StrategyState.RUNNING:
                continue
            if self._portfolio_snapshot is not None:
                self._manager.update_portfolio_snapshot(
                    managed.entity.strategy_id,
                    self._portfolio_snapshot,
                )
            raw_signal = self._executor.execute_portfolio_changed(
                managed.instance,
                managed.context,
                payload,
            )
            result = self._process_signal(
                raw_signal,
                managed=managed,
                event_name="strategy.portfolio.processed",
                reason="portfolio_changed",
            )
            if result is not None:
                results.append(result)
        return results

    def _process_signal(
        self,
        raw_signal: TradingSignal | None,
        *,
        managed: ManagedStrategy,
        event_name: str,
        reason: str,
    ) -> SignalResult | None:
        if raw_signal is None:
            return None

        signal = self._generator.from_strategy_output(
            strategy_id=managed.entity.strategy_id,
            strategy_name=managed.entity.name,
            output=raw_signal,
        )
        result = self._evaluator.evaluate(signal, context=managed.context)
        if not result.evaluated:
            return result

        self._manager.record_signal(managed.entity.strategy_id, signal)
        if result.accepted:
            self._publish_strategy_event(signal, event_name=event_name, reason=reason)
        return result

    def _publish_strategy_event(
        self,
        signal: TradingSignal,
        *,
        event_name: str,
        reason: str,
    ) -> None:
        if self._event_bus is None:
            return
        self._event_bus.publish(
            StrategyEvent(
                source=self._source,
                event_name=event_name,
                payload={
                    "reason": reason,
                    "signal_id": signal.signal_id,
                    "strategy_id": signal.strategy_id,
                    "strategy_name": signal.strategy_name,
                    "symbol_code": signal.symbol_code,
                    "signal_type": signal.signal_type.value,
                    "price": str(signal.price),
                    "quantity": str(signal.quantity),
                    "confidence": str(signal.confidence),
                    "timestamp": signal.timestamp.isoformat(),
                    "message": signal.reason,
                },
                correlation_id=signal.signal_id,
            )
        )
        self._logger.info(
            "Strategy signal published strategy=%s symbol=%s type=%s",
            signal.strategy_name,
            signal.symbol_code,
            signal.signal_type.value,
        )
