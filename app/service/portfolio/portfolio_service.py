"""Portfolio application service."""

from __future__ import annotations

import logging
from typing import Any

from app.core.logging import CorrelationContext, LogCategory, get_logger
from app.domain.portfolio.portfolio_snapshot import PortfolioSnapshot
from app.events.event_bus_service import EventBusService
from app.portfolio.in_memory_portfolio_store import InMemoryPortfolioStore
from app.portfolio.portfolio_engine import PortfolioEngine
from app.portfolio.portfolio_event_handler import PortfolioEventHandler
from app.repository.interfaces.portfolio_repository import PortfolioRepository


def _resolve_logger() -> logging.Logger:
    try:
        return get_logger(__name__, category=LogCategory.SYSTEM)
    except RuntimeError:
        return logging.getLogger(__name__)


class PortfolioService:
    """External entry point for portfolio state management."""

    def __init__(
        self,
        *,
        store: InMemoryPortfolioStore | None = None,
        engine: PortfolioEngine | None = None,
        event_handler: PortfolioEventHandler | None = None,
        event_bus: EventBusService | None = None,
        account_no: str = "",
        portfolio_repository: PortfolioRepository | None = None,
    ) -> None:
        self._account_no = account_no
        self._portfolio_repository = portfolio_repository
        self._store = store or InMemoryPortfolioStore(account_no=account_no)
        snapshot_listener = self._persist_snapshot if portfolio_repository is not None else None
        self._event_bus = event_bus
        self._engine = engine or PortfolioEngine(
            store=self._store,
            event_bus=event_bus,
            snapshot_listener=snapshot_listener,
        )
        self._handler = event_handler or PortfolioEventHandler(engine=self._engine)
        self._logger = _resolve_logger()
        self._started = False

    @property
    def engine(self) -> PortfolioEngine:
        return self._engine

    @property
    def event_handler(self) -> PortfolioEventHandler:
        return self._handler

    @property
    def portfolio_repository(self) -> PortfolioRepository | None:
        """Return the optional portfolio persistence repository."""
        return self._portfolio_repository

    def start(self, event_bus: EventBusService | None = None) -> None:
        """Register portfolio handlers with EventBus."""
        self._restore_portfolio()
        bus = event_bus or self._event_bus
        if bus is None:
            msg = "EventBusService is required to start portfolio subscriptions"
            raise ValueError(msg)
        self._handler.register(bus)
        self._started = True
        self._logger.info("PortfolioService started with EventBus subscriptions")

    def stop(self, event_bus: EventBusService | None = None) -> None:
        """Unregister portfolio handlers from EventBus."""
        bus = event_bus or self._event_bus
        if bus is not None and self._started:
            self._handler.unregister(bus)
            self._started = False

    def get_snapshot(self) -> PortfolioSnapshot:
        """Return the current portfolio snapshot."""
        return self._engine.get_snapshot()

    def apply_account(self, payload: dict[str, Any]) -> PortfolioSnapshot:
        """Apply account data directly via service (non-EventBus path)."""
        with CorrelationContext():
            return self._engine.apply_account(payload)

    def apply_execution(self, payload: dict[str, Any]) -> PortfolioSnapshot:
        """Apply execution data directly via service."""
        with CorrelationContext():
            return self._engine.apply_execution(payload)

    def apply_market_data(self, payload: dict[str, Any]) -> PortfolioSnapshot:
        """Apply market data directly via service."""
        with CorrelationContext():
            return self._engine.apply_market_data(payload)

    def _restore_portfolio(self) -> None:
        if self._portfolio_repository is None:
            return
        snapshot = self._portfolio_repository.get_latest_snapshot(self._account_no)
        if snapshot is None:
            return
        self._store.load_snapshot(snapshot)
        self._logger.info(
            "Portfolio restored from repository account_no=%s positions=%s",
            snapshot.account_no,
            len(snapshot.positions),
        )

    def _persist_snapshot(self, snapshot: PortfolioSnapshot) -> None:
        if self._portfolio_repository is None:
            return
        try:
            self._portfolio_repository.save_portfolio(snapshot)
        except Exception:
            self._logger.exception(
                "Failed to persist portfolio snapshot account_no=%s",
                snapshot.account_no,
            )


def build_portfolio_service(
    *,
    event_bus: EventBusService | None = None,
    account_no: str = "",
    portfolio_repository: PortfolioRepository | None = None,
) -> PortfolioService:
    """Create a PortfolioService wired with default components."""
    return PortfolioService(
        event_bus=event_bus,
        account_no=account_no,
        portfolio_repository=portfolio_repository,
    )
