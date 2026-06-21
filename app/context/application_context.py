"""Runtime application context holding wired KATS services."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from app.broker.kis.auth import AuthenticationComponents
from app.config.config_manager import ConfigManager
from app.core.logging.logger_service import LoggerService
from app.database.database_manager import DatabaseManager
from app.events.event_bus_service import EventBusService
from app.plugins.plugin_manager import PluginLoadReport, PluginManager
from app.scheduler.rules import IntervalRule
from app.scheduler.scheduled_task import ScheduledTask
from app.scheduler.task_types import ScheduledTaskType
from app.service.backtest.backtest_service import BacktestService
from app.service.notification.notification_service import NotificationService
from app.service.order.order_service import OrderService
from app.service.portfolio.portfolio_service import PortfolioService
from app.service.risk.risk_service import RiskService
from app.service.scheduler.scheduler_service import SchedulerService
from app.service.strategy.strategy_service import StrategyService

if TYPE_CHECKING:
    from app.config.app_settings import AppSettings
    from app.service.websocket.websocket_service import WebSocketService

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ApplicationContext:
    """Container for the fully wired KATS runtime."""

    project_root: Path
    settings: AppSettings
    config_manager: ConfigManager
    logger_service: LoggerService
    database_manager: DatabaseManager
    event_bus: EventBusService
    portfolio_service: PortfolioService
    strategy_service: StrategyService
    risk_service: RiskService
    backtest_service: BacktestService
    notification_service: NotificationService
    authentication: AuthenticationComponents | None = None
    order_service: OrderService | None = None
    websocket_service: WebSocketService | None = None
    scheduler_service: SchedulerService | None = None
    plugin_manager: PluginManager | None = None
    plugin_load_report: PluginLoadReport | None = None
    _running: bool = field(default=False, init=False)

    @property
    def is_running(self) -> bool:
        """Return True when runtime services are started."""
        return self._running

    @property
    def is_websocket_connected(self) -> bool:
        """Return websocket connection status."""
        if self.websocket_service is None:
            return False
        return self.websocket_service.is_connected

    def start(self) -> None:
        """Start runtime services in dependency order."""
        if self._running:
            return

        self.notification_service.start(self.event_bus)
        self.portfolio_service.start(self.event_bus)
        self.strategy_service.start(self.event_bus)
        self.risk_service.start(self.event_bus)

        if self.scheduler_service is not None and self.settings.config.scheduler.enabled:
            self._register_scheduler_tasks()
            self.scheduler_service.start(self.event_bus)

        self._running = True
        logger.info("ApplicationContext started")

    def stop(self) -> None:
        """Stop runtime services in reverse dependency order."""
        if not self._running:
            return

        if self.websocket_service is not None and self.websocket_service.is_connected:
            self.websocket_service.disconnect()

        if self.scheduler_service is not None and self.settings.config.scheduler.enabled:
            self.scheduler_service.stop(self.event_bus)

        self.risk_service.stop(self.event_bus)
        self.strategy_service.stop(self.event_bus)
        self.portfolio_service.stop(self.event_bus)
        self.notification_service.stop(self.event_bus)

        self._running = False
        logger.info("ApplicationContext stopped")

    def connect_websocket(self) -> None:
        """Explicitly connect the WebSocket client."""
        if self.websocket_service is None:
            msg = "WebSocketService is not configured"
            raise RuntimeError(msg)
        self.websocket_service.connect()
        logger.info("WebSocket connected explicitly")

    def disconnect_websocket(self) -> None:
        """Explicitly disconnect the WebSocket client."""
        if self.websocket_service is None:
            return
        if self.websocket_service.is_connected:
            self.websocket_service.disconnect()
            logger.info("WebSocket disconnected")

    def shutdown(self) -> None:
        """Stop services and release logging resources."""
        self.stop()
        self.logger_service.shutdown()

    def _register_scheduler_tasks(self) -> None:
        if self.scheduler_service is None:
            return

        scheduler_config = self.settings.config.scheduler
        strategy_config = self.settings.config.strategy

        if (
            scheduler_config.strategy_auto_start
            and strategy_config.auto_start
            and scheduler_config.strategy_auto_start_id
        ):
            self.scheduler_service.register_task(
                ScheduledTask(
                    task_id="strategy-auto-start",
                    task_type=ScheduledTaskType.STRATEGY_AUTO_START,
                    rule=IntervalRule(interval_seconds=strategy_config.scan_interval_seconds),
                    payload={"strategy_id": scheduler_config.strategy_auto_start_id},
                    description="Auto-start configured strategy",
                )
            )

        self.scheduler_service.register_task(
            ScheduledTask(
                task_id="log-cleanup",
                task_type=ScheduledTaskType.LOG_CLEANUP,
                rule=IntervalRule(interval_seconds=scheduler_config.log_cleanup_interval_seconds),
                payload={"max_age_days": 7},
                description="Rotate and purge old log files",
            )
        )
