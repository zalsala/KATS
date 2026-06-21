"""Risk application service."""

from __future__ import annotations

import logging
from typing import Any

from app.core.logging import CorrelationContext, LogCategory, get_logger
from app.domain.portfolio.portfolio_snapshot import PortfolioSnapshot
from app.domain.risk.risk_policy import RiskPolicy
from app.domain.risk.risk_result import RiskResult
from app.domain.strategy.trading_signal import TradingSignal
from app.events.event_bus_service import EventBusService
from app.risk.risk_engine import RiskEngine
from app.risk.risk_evaluator import RiskEvaluator
from app.risk.risk_event_handler import RiskEventHandler
from app.risk.risk_manager import RiskManager
from app.service.portfolio.portfolio_service import PortfolioService


def _resolve_logger() -> logging.Logger:
    try:
        return get_logger(__name__, category=LogCategory.ORDER)
    except RuntimeError:
        return logging.getLogger(__name__)


class RiskService:
    """External entry point for risk validation."""

    def __init__(
        self,
        *,
        portfolio_service: PortfolioService,
        manager: RiskManager | None = None,
        engine: RiskEngine | None = None,
        event_handler: RiskEventHandler | None = None,
        event_bus: EventBusService | None = None,
        policy: RiskPolicy | None = None,
    ) -> None:
        self._portfolio_service = portfolio_service
        self._event_bus = event_bus
        self._manager = manager or RiskManager()
        self._engine = engine or RiskEngine(
            portfolio_service=portfolio_service,
            manager=self._manager,
            evaluator=RiskEvaluator(),
            policy=policy,
            event_bus=event_bus,
        )
        self._handler = event_handler or RiskEventHandler(engine=self._engine)
        self._logger = _resolve_logger()
        self._started = False

    @property
    def engine(self) -> RiskEngine:
        return self._engine

    @property
    def manager(self) -> RiskManager:
        return self._manager

    @property
    def event_handler(self) -> RiskEventHandler:
        return self._handler

    def start(self, event_bus: EventBusService | None = None) -> None:
        """Register risk handlers with EventBus."""
        bus = event_bus or self._event_bus
        if bus is None:
            msg = "EventBusService is required to start risk subscriptions"
            raise ValueError(msg)
        self._handler.register(bus)
        self._started = True
        self._logger.info("RiskService started with EventBus subscriptions")

    def stop(self, event_bus: EventBusService | None = None) -> None:
        """Unregister risk handlers from EventBus."""
        bus = event_bus or self._event_bus
        if bus is not None and self._started:
            self._handler.unregister(bus)
            self._started = False

    def set_policy(self, policy: RiskPolicy) -> None:
        """Update active risk policy."""
        self._engine.set_policy(policy)

    def set_emergency_stop(self, active: bool) -> None:
        """Enable or disable emergency stop."""
        self._manager.set_emergency_stop(active)

    def validate_strategy_payload(self, payload: dict[str, Any]) -> RiskResult:
        """Validate a strategy event payload."""
        with CorrelationContext():
            return self._engine.handle_strategy_signal(payload)

    def validate_signal(
        self,
        signal: TradingSignal,
        *,
        portfolio: PortfolioSnapshot | None = None,
    ) -> RiskResult:
        """Validate a trading signal directly."""
        with CorrelationContext():
            return self._engine.validate_signal(signal, portfolio=portfolio)


def build_risk_service(
    *,
    portfolio_service: PortfolioService,
    event_bus: EventBusService | None = None,
    policy: RiskPolicy | None = None,
) -> RiskService:
    """Create a RiskService wired with default components."""
    return RiskService(
        portfolio_service=portfolio_service,
        event_bus=event_bus,
        policy=policy,
    )
