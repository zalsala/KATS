"""Strategy application service."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any

from app.core.logging import CorrelationContext, LogCategory, get_logger
from app.database.database_manager import DatabaseManager
from app.domain.strategy.signal_result import SignalResult
from app.domain.strategy.strategy import Strategy
from app.domain.strategy.strategy_state import StrategyState
from app.dto.strategy.mappers.strategy_mappers import StrategyMapper
from app.dto.strategy.strategy_dto import StrategyDto
from app.events.event_bus_service import EventBusService
from app.plugins.plugin_manager import load_plugins_into_strategy_registry
from app.repository.in_memory_strategy_repository import InMemoryStrategyRepository
from app.repository.interfaces.strategy_repository import StrategyRepository
from app.strategy.default_registry import register_default_strategies
from app.strategy.signal_evaluator import SignalEvaluator
from app.strategy.signal_generator import SignalGenerator
from app.strategy.strategy_engine import StrategyEngine
from app.strategy.strategy_event_handler import StrategyEventHandler
from app.strategy.strategy_executor import StrategyExecutor
from app.strategy.strategy_manager import StrategyManager
from app.strategy.strategy_registry import StrategyRegistry


def _resolve_logger() -> logging.Logger:
    try:
        return get_logger(__name__, category=LogCategory.SYSTEM)
    except RuntimeError:
        return logging.getLogger(__name__)


class StrategyService:
    """External entry point for strategy management and execution."""

    def __init__(
        self,
        *,
        repository: StrategyRepository | None = None,
        registry: StrategyRegistry | None = None,
        manager: StrategyManager | None = None,
        engine: StrategyEngine | None = None,
        event_handler: StrategyEventHandler | None = None,
        event_bus: EventBusService | None = None,
    ) -> None:
        self._repository = repository or InMemoryStrategyRepository()
        self._registry = registry or StrategyRegistry()
        register_default_strategies(self._registry)
        self._manager = manager or StrategyManager(registry=self._registry)
        self._event_bus = event_bus
        self._engine = engine or StrategyEngine(
            manager=self._manager,
            executor=StrategyExecutor(),
            signal_generator=SignalGenerator(),
            signal_evaluator=SignalEvaluator(),
            event_bus=event_bus,
        )
        self._handler = event_handler or StrategyEventHandler(engine=self._engine)
        self._logger = _resolve_logger()
        self._started = False

    @property
    def engine(self) -> StrategyEngine:
        return self._engine

    @property
    def manager(self) -> StrategyManager:
        return self._manager

    @property
    def registry(self) -> StrategyRegistry:
        return self._registry

    @property
    def event_handler(self) -> StrategyEventHandler:
        return self._handler

    def start(self, event_bus: EventBusService | None = None) -> None:
        """Register strategy handlers with EventBus."""
        bus = event_bus or self._event_bus
        if bus is None:
            msg = "EventBusService is required to start strategy subscriptions"
            raise ValueError(msg)
        self._handler.register(bus)
        self._started = True
        self._logger.info("StrategyService started with EventBus subscriptions")

    def stop(self, event_bus: EventBusService | None = None) -> None:
        """Unregister strategy handlers from EventBus."""
        bus = event_bus or self._event_bus
        if bus is not None and self._started:
            self._handler.unregister(bus)
            self._started = False

    def register_strategy(
        self,
        *,
        strategy_type: str,
        name: str,
        symbols: list[str],
        parameters: dict[str, Any] | None = None,
        enabled: bool = True,
        auto_start: bool = False,
    ) -> StrategyDto:
        """Register a new strategy instance."""
        with CorrelationContext():
            if not self._registry.is_registered(strategy_type):
                msg = f"Unknown strategy type: {strategy_type}"
                raise ValueError(msg)
            strategy_id = str(uuid.uuid4())
            entity = Strategy(
                strategy_id=strategy_id,
                name=name,
                strategy_type=strategy_type,
                enabled=enabled,
                parameters=parameters or {},
                symbols=tuple(symbols),
                state=StrategyState.CREATED,
            )
            self._repository.save(entity)
            self._manager.register(entity)
            if auto_start and enabled:
                self._manager.start(strategy_id)
                self._repository.save(entity)
            self._logger.info(
                "Strategy registered id=%s type=%s name=%s",
                strategy_id,
                strategy_type,
                name,
            )
            return StrategyMapper.to_dto(entity)

    def start_strategy(self, strategy_id: str) -> StrategyDto:
        """Start a registered strategy."""
        with CorrelationContext():
            self._manager.start(strategy_id)
            entity = self._repository.get(strategy_id)
            if entity is None:
                msg = f"Strategy not found: {strategy_id}"
                raise KeyError(msg)
            self._repository.save(entity)
            return StrategyMapper.to_dto(entity)

    def stop_strategy(self, strategy_id: str) -> StrategyDto:
        """Stop a running strategy."""
        with CorrelationContext():
            self._manager.stop(strategy_id)
            entity = self._repository.get(strategy_id)
            if entity is None:
                msg = f"Strategy not found: {strategy_id}"
                raise KeyError(msg)
            self._repository.save(entity)
            return StrategyMapper.to_dto(entity)

    def list_strategies(self) -> list[StrategyDto]:
        """Return all registered strategies."""
        return [StrategyMapper.to_dto(item) for item in self._repository.list_all()]

    def get_strategy(self, strategy_id: str) -> StrategyDto | None:
        """Return a strategy by ID."""
        entity = self._repository.get(strategy_id)
        return StrategyMapper.to_dto(entity) if entity else None

    def handle_market_data(self, payload: dict[str, Any]) -> list[SignalResult]:
        """Apply market data directly via service."""
        with CorrelationContext():
            return self._engine.handle_market_data(payload)


def build_strategy_service(
    *,
    event_bus: EventBusService | None = None,
    registry: StrategyRegistry | None = None,
    plugins_root: Path | None = None,
    load_plugins: bool = False,
    repository: StrategyRepository | None = None,
    database_manager: DatabaseManager | None = None,
) -> StrategyService:
    """Create a StrategyService wired with default components."""
    strategy_registry = registry or StrategyRegistry()
    if registry is None:
        register_default_strategies(strategy_registry)
    if load_plugins and plugins_root is not None:
        load_plugins_into_strategy_registry(
            plugins_root=plugins_root,
            strategy_registry=strategy_registry,
        )
    strategy_repository = repository
    if strategy_repository is None and database_manager is not None:
        database_manager.initialize()
        strategy_repository = database_manager.build_strategy_repository()
    return StrategyService(
        registry=strategy_registry,
        repository=strategy_repository,
        event_bus=event_bus,
    )
