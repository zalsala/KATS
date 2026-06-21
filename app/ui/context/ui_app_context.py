"""UI application context with wired services."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from app.bootstrap.application_bootstrap import ApplicationBootstrap, BootstrapOptions
from app.config.config_manager import ConfigManager
from app.context.application_context import ApplicationContext
from app.events.event_bus_service import EventBusService
from app.service.backtest.backtest_service import BacktestService
from app.service.order.order_service import OrderService
from app.service.portfolio.portfolio_service import PortfolioService
from app.service.risk.risk_service import RiskService
from app.service.strategy.strategy_service import StrategyService

if TYPE_CHECKING:
    from app.service.websocket.websocket_service import WebSocketService


@dataclass(slots=True)
class UiAppContext:
    """Container for services used by the desktop UI."""

    config_manager: ConfigManager
    event_bus: EventBusService
    portfolio_service: PortfolioService
    strategy_service: StrategyService
    risk_service: RiskService
    backtest_service: BacktestService
    order_service: OrderService | None = None
    websocket_service: WebSocketService | None = None
    application_context: ApplicationContext | None = None
    _started: bool = False

    @classmethod
    def create(
        cls,
        *,
        project_root: Path | None = None,
        order_service: OrderService | None = None,
        websocket_service: WebSocketService | None = None,
    ) -> UiAppContext:
        """Build UI context using the shared application bootstrap."""
        root = project_root or Path.cwd()
        bootstrap = ApplicationBootstrap(
            root,
            options=BootstrapOptions(
                setup_logging=False,
                validate_runtime=False,
                enable_ui_notifications=True,
            ),
        )
        application_context = bootstrap.bootstrap()
        ui_context = cls.from_application_context(application_context)
        if order_service is not None:
            ui_context.order_service = order_service
        if websocket_service is not None:
            ui_context.websocket_service = websocket_service
        return ui_context

    @classmethod
    def from_application_context(cls, application_context: ApplicationContext) -> UiAppContext:
        """Create a UI context view over a shared ApplicationContext."""
        return cls(
            config_manager=application_context.config_manager,
            event_bus=application_context.event_bus,
            portfolio_service=application_context.portfolio_service,
            strategy_service=application_context.strategy_service,
            risk_service=application_context.risk_service,
            backtest_service=application_context.backtest_service,
            order_service=application_context.order_service,
            websocket_service=application_context.websocket_service,
            application_context=application_context,
        )

    def start(self) -> None:
        """Start EventBus subscriptions for runtime services."""
        if self._started:
            return
        if self.application_context is not None:
            self.application_context.start()
        else:
            self.portfolio_service.start(self.event_bus)
            self.strategy_service.start(self.event_bus)
            self.risk_service.start(self.event_bus)
        self._started = True

    def stop(self) -> None:
        """Stop EventBus subscriptions."""
        if not self._started:
            return
        if self.application_context is not None:
            self.application_context.stop()
        else:
            self.risk_service.stop(self.event_bus)
            self.strategy_service.stop(self.event_bus)
            self.portfolio_service.stop(self.event_bus)
        self._started = False

    @property
    def is_connected(self) -> bool:
        """Return websocket connection status."""
        if self.websocket_service is None:
            return False
        return self.websocket_service.is_connected
