"""Database lifecycle manager."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from app.config.config_manager import ConfigManager
from app.database.connection.sqlite_connection_factory import SQLiteConnectionFactory
from app.database.migration.migration_manager import MigrationManager

if TYPE_CHECKING:
    from app.database.repositories.sqlite_backtest_repository import SQLiteBacktestRepository
    from app.database.repositories.sqlite_notification_repository import (
        SQLiteNotificationRepository,
    )
    from app.database.repositories.sqlite_order_repository import SQLiteOrderRepository
    from app.database.repositories.sqlite_portfolio_repository import SQLitePortfolioRepository
    from app.database.repositories.sqlite_risk_policy_repository import SQLiteRiskPolicyRepository
    from app.database.repositories.sqlite_strategy_repository import SQLiteStrategyRepository
    from app.database.repositories.sqlite_system_state_repository import SQLiteSystemStateRepository

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Initialize SQLite access and run migrations from configuration."""

    def __init__(
        self,
        *,
        database_path: Path,
        migration_enabled: bool = True,
        connection_factory: SQLiteConnectionFactory | None = None,
        migration_manager: MigrationManager | None = None,
    ) -> None:
        self._database_path = database_path
        self._migration_enabled = migration_enabled
        self._connection_factory = connection_factory or SQLiteConnectionFactory(
            database_path=database_path
        )
        self._migration_manager = migration_manager or MigrationManager(
            connection_factory=self._connection_factory
        )
        self._initialized = False

    @property
    def database_path(self) -> Path:
        return self._database_path

    @property
    def connection_factory(self) -> SQLiteConnectionFactory:
        return self._connection_factory

    @property
    def migration_manager(self) -> MigrationManager:
        return self._migration_manager

    @classmethod
    def from_config_manager(cls, config_manager: ConfigManager) -> DatabaseManager:
        """Build a DatabaseManager using ConfigManager database settings."""
        settings = config_manager.get_settings()
        database_path = settings.resolve_path(settings.config.database.database_path)
        return cls(
            database_path=database_path,
            migration_enabled=settings.config.database.migration_enabled,
        )

    def initialize(self) -> list[str]:
        """Prepare the database and apply pending migrations."""
        if self._initialized:
            return []
        applied: list[str] = []
        if self._migration_enabled:
            applied = self._migration_manager.migrate()
        self._initialized = True
        logger.info("Database initialized path=%s migrations=%s", self._database_path, applied)
        return applied

    def build_order_repository(self) -> SQLiteOrderRepository:
        from app.database.repositories.sqlite_order_repository import SQLiteOrderRepository

        return SQLiteOrderRepository(connection_factory=self._connection_factory)

    def build_portfolio_repository(self) -> SQLitePortfolioRepository:
        from app.database.repositories.sqlite_portfolio_repository import SQLitePortfolioRepository

        return SQLitePortfolioRepository(connection_factory=self._connection_factory)

    def build_strategy_repository(self) -> SQLiteStrategyRepository:
        from app.database.repositories.sqlite_strategy_repository import SQLiteStrategyRepository

        return SQLiteStrategyRepository(connection_factory=self._connection_factory)

    def build_risk_policy_repository(self) -> SQLiteRiskPolicyRepository:
        from app.database.repositories.sqlite_risk_policy_repository import (
            SQLiteRiskPolicyRepository,
        )

        return SQLiteRiskPolicyRepository(connection_factory=self._connection_factory)

    def build_backtest_repository(self) -> SQLiteBacktestRepository:
        from app.database.repositories.sqlite_backtest_repository import SQLiteBacktestRepository

        return SQLiteBacktestRepository(connection_factory=self._connection_factory)

    def build_notification_repository(self) -> SQLiteNotificationRepository:
        from app.database.repositories.sqlite_notification_repository import (
            SQLiteNotificationRepository,
        )

        return SQLiteNotificationRepository(connection_factory=self._connection_factory)

    def build_system_state_repository(self) -> SQLiteSystemStateRepository:
        from app.database.repositories.sqlite_system_state_repository import (
            SQLiteSystemStateRepository,
        )

        return SQLiteSystemStateRepository(connection_factory=self._connection_factory)
