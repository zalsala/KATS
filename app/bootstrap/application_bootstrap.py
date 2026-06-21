"""KATS application bootstrap and startup orchestration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from app.bootstrap.health_check import HealthCheck
from app.bootstrap.service_wiring import wire_application_context
from app.broker.kis.auth.http_transport import HttpTransport
from app.broker.kis.rest.http_transport import RestHttpTransport
from app.broker.kis.websocket.ws_transport import WsTransport
from app.config.config_manager import ConfigManager
from app.context.application_context import ApplicationContext
from app.core.constants import DOTENV_FILE_NAME
from app.core.logging import setup_logging
from app.core.logging.logger_service import LoggerService
from app.database.database_manager import DatabaseManager
from app.release.exceptions import ReleaseValidationError
from app.release.runtime_validator import RuntimeValidator

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class BootstrapOptions:
    """Options controlling application bootstrap behavior."""

    setup_logging: bool = True
    validate_runtime: bool = True
    enable_ui_notifications: bool = False
    ws_transport: WsTransport | None = None
    auth_transport: HttpTransport | None = None
    rest_transport: RestHttpTransport | None = None


class ApplicationBootstrap:
    """Compose and initialize the KATS runtime."""

    def __init__(
        self,
        project_root: Path,
        *,
        environment: str | None = None,
        options: BootstrapOptions | None = None,
    ) -> None:
        self._project_root = project_root
        self._environment = environment
        self._options = options or BootstrapOptions()

    def bootstrap(self) -> ApplicationContext:
        """Initialize Config → Logging → Database → EventBus → Services."""
        config_manager = ConfigManager.get_instance(
            project_root=self._project_root,
            environment=self._environment,
        )
        settings = config_manager.load()

        if self._options.validate_runtime:
            dotenv_path = self._project_root / DOTENV_FILE_NAME
            RuntimeValidator().validate_startup(settings, dotenv_path=dotenv_path)

        logger_service = LoggerService.get_instance()
        if self._options.setup_logging:
            setup_logging(settings.config.logging, self._project_root / "logs")

        database_manager = DatabaseManager.from_config_manager(config_manager)
        database_manager.initialize()

        context = wire_application_context(
            project_root=self._project_root,
            settings=settings,
            config_manager=config_manager,
            logger_service=logger_service,
            database_manager=database_manager,
            enable_ui_notifications=self._options.enable_ui_notifications,
            ws_transport=self._options.ws_transport,
            auth_transport=self._options.auth_transport,
            rest_transport=self._options.rest_transport,
        )
        logger.info(
            "Application bootstrap completed (environment=%s, scheduler=%s, websocket=%s)",
            settings.environment,
            settings.config.scheduler.enabled,
            context.websocket_service is not None,
        )
        return context

    def run(self) -> ApplicationContext:
        """Bootstrap, start services, and run health checks."""
        context = self.bootstrap()
        context.start()
        health = HealthCheck().run(context)
        logger.info("Health check: %s", health.summary())
        if not health.healthy:
            msg = f"Health check failed: {health.summary()}"
            raise ReleaseValidationError(msg)
        return context
