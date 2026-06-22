"""Service wiring for application bootstrap."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from app.bootstrap.broker_wiring import (
    build_authentication,
    build_order_service,
    build_websocket_service_from_settings,
)
from app.bootstrap.plugin_wiring import wire_strategy_plugins
from app.broker.kis.websocket.ws_transport import WsTransport
from app.config.config_manager import ConfigManager
from app.context.application_context import ApplicationContext
from app.core.logging.logger_service import LoggerService
from app.database.database_manager import DatabaseManager
from app.events.event_bus_service import EventBusService, build_event_bus_service
from app.service.backtest.backtest_service import build_backtest_service
from app.service.chart.chart_service import build_chart_service
from app.service.notification.notification_service import build_notification_service
from app.service.portfolio.portfolio_service import build_portfolio_service
from app.service.risk.risk_service import build_risk_service
from app.service.scheduler.scheduler_service import build_scheduler_service
from app.service.scheduler.scheduler_worker_service import build_scheduler_worker_service
from app.service.strategy.strategy_service import build_strategy_service

if TYPE_CHECKING:
    from app.broker.kis.auth.http_transport import HttpTransport
    from app.broker.kis.rest.http_transport import RestHttpTransport
    from app.config.app_settings import AppSettings


def wire_application_context(
    *,
    project_root: Path,
    settings: AppSettings,
    config_manager: ConfigManager,
    logger_service: LoggerService,
    database_manager: DatabaseManager,
    event_bus: EventBusService | None = None,
    enable_ui_notifications: bool = False,
    ws_transport: WsTransport | None = None,
    rest_transport: RestHttpTransport | None = None,
    auth_transport: HttpTransport | None = None,
) -> ApplicationContext:
    """Wire all KATS services into an ApplicationContext."""
    bus = event_bus or build_event_bus_service()
    account_no = settings.secrets.account_no or "00000000"

    authentication = build_authentication(settings, transport=auth_transport)
    strategy_registry, plugin_manager, plugin_load_report = wire_strategy_plugins(
        project_root=project_root,
        auto_load=settings.config.strategy.auto_load,
    )
    strategy_service = build_strategy_service(
        event_bus=bus,
        registry=strategy_registry,
        load_plugins=False,
        database_manager=database_manager,
    )
    portfolio_repository = database_manager.build_portfolio_repository()
    portfolio_service = build_portfolio_service(
        event_bus=bus,
        account_no=account_no,
        portfolio_repository=portfolio_repository,
    )
    risk_service = build_risk_service(portfolio_service=portfolio_service, event_bus=bus)
    backtest_service = build_backtest_service()
    chart_service = build_chart_service(event_bus=bus)
    notification_service = build_notification_service(
        event_bus=bus,
        database_manager=database_manager,
        notification_registry=plugin_manager.notification_registry if plugin_manager else None,
        enable_console=True,
        enable_ui=enable_ui_notifications,
        enable_plugins=plugin_manager is not None,
    )

    scheduler_service = None
    scheduler_worker_service = None
    if settings.config.scheduler.enabled:
        scheduler_service = build_scheduler_service(
            event_bus=bus,
            strategy_service=strategy_service,
            backtest_service=backtest_service,
            portfolio_service=portfolio_service,
            plugin_manager=plugin_manager,
            logger_service=logger_service,
        )
        scheduler_worker_service = build_scheduler_worker_service(
            scheduler_service,
            interval_seconds=settings.config.scheduler.tick_interval_seconds,
        )

    order_service = build_order_service(
        settings=settings,
        auth=authentication,
        database_manager=database_manager,
        rest_transport=rest_transport,
    )
    websocket_service = build_websocket_service_from_settings(
        settings=settings,
        auth=authentication,
        ws_transport=ws_transport,
    )

    return ApplicationContext(
        project_root=project_root,
        settings=settings,
        config_manager=config_manager,
        logger_service=logger_service,
        database_manager=database_manager,
        event_bus=bus,
        portfolio_service=portfolio_service,
        portfolio_repository=portfolio_repository,
        strategy_service=strategy_service,
        risk_service=risk_service,
        backtest_service=backtest_service,
        chart_service=chart_service,
        notification_service=notification_service,
        authentication=authentication,
        order_service=order_service,
        websocket_service=websocket_service,
        scheduler_service=scheduler_service,
        scheduler_worker_service=scheduler_worker_service,
        plugin_manager=plugin_manager,
        plugin_load_report=plugin_load_report,
    )
