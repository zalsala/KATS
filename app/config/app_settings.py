"""Immutable runtime application settings."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from app.core.constants import (
    ENV_PRODUCTION,
    ENV_SIMULATION,
    KIS_ACCOUNT_MOCK,
    KIS_ACCOUNT_REAL,
    KIS_REAL_REST_BASE_URL,
    KIS_VTS_REST_BASE_URL,
)

if TYPE_CHECKING:
    from app.config.config_models import KatsConfig
    from app.config.secret_manager import KisSecrets


@dataclass(frozen=True, slots=True)
class AppSettings:
    """Immutable snapshot of validated runtime configuration.

    Combines non-sensitive ``KatsConfig`` with KIS OpenAPI secrets managed
    separately by ``SecretManager``.

    Attributes:
        project_root: Absolute path to the project root directory.
        config: Validated non-secret configuration model.
        secrets: KIS OpenAPI credentials loaded from environment sources.
    """

    project_root: Path
    config: KatsConfig
    secrets: KisSecrets

    @property
    def environment(self) -> str:
        """Return the active runtime environment name."""
        return self.config.environment

    @property
    def is_production(self) -> bool:
        """Return True when running in production environment."""
        return self.config.environment == ENV_PRODUCTION

    @property
    def is_simulation(self) -> bool:
        """Return True when running in simulation (mock trading) environment."""
        return self.config.environment == ENV_SIMULATION

    @property
    def is_mock_account(self) -> bool:
        """Return True when connected to a KIS mock (VTS) account."""
        return self.secrets.account_type == KIS_ACCOUNT_MOCK

    @property
    def is_real_account(self) -> bool:
        """Return True when connected to a KIS real account."""
        return self.secrets.account_type == KIS_ACCOUNT_REAL

    @property
    def kis_rest_base_url(self) -> str:
        """Return the effective KIS REST base URL for the current environment."""
        return self.config.broker.base_url

    @property
    def kis_websocket_url(self) -> str:
        """Return the effective KIS WebSocket URL for the current environment."""
        return self.config.broker.websocket_url

    @property
    def uses_vts_endpoint(self) -> bool:
        """Return True when broker REST URL points to the KIS VTS (mock) server."""
        return KIS_VTS_REST_BASE_URL in self.config.broker.base_url

    @property
    def uses_real_endpoint(self) -> bool:
        """Return True when broker REST URL points to the KIS real server."""
        return KIS_REAL_REST_BASE_URL in self.config.broker.base_url

    @classmethod
    def create(
        cls,
        project_root: Path,
        config: KatsConfig,
        secrets: KisSecrets,
    ) -> AppSettings:
        """Build an ``AppSettings`` instance from validated components.

        Args:
            project_root: Project root directory.
            config: Validated configuration model.
            secrets: Loaded KIS API secrets.

        Returns:
            Immutable application settings snapshot.
        """
        return cls(
            project_root=project_root.resolve(),
            config=config,
            secrets=secrets,
        )

    def resolve_path(self, relative_path: str) -> Path:
        """Resolve a relative path against the project root.

        Args:
            relative_path: Path relative to project root.

        Returns:
            Absolute resolved path.
        """
        path = Path(relative_path)
        if path.is_absolute():
            return path
        return self.project_root / path
