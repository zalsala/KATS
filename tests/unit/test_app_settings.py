"""Unit tests for AppSettings."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.config.app_settings import AppSettings
from app.config.config_models import ApplicationConfig, BrokerConfig, KatsConfig
from app.config.secret_manager import KisSecrets
from app.core.constants import ENV_PRODUCTION, ENV_SIMULATION, KIS_VTS_REST_BASE_URL

pytestmark = pytest.mark.unit


def _make_config(environment: str, base_url: str) -> KatsConfig:
    """Build a minimal KatsConfig for testing."""
    return KatsConfig(
        application=ApplicationConfig(),
        broker=BrokerConfig(
            base_url=base_url,
            websocket_url="ws://ops.koreainvestment.com:21000",
        ),
        environment=environment,  # type: ignore[arg-type]
    )


class TestAppSettings:
    """Tests for AppSettings dataclass."""

    def test_create_returns_frozen_instance(self, tmp_path: Path) -> None:
        """AppSettings.create returns an immutable instance."""
        config = _make_config(ENV_SIMULATION, KIS_VTS_REST_BASE_URL)
        secrets = KisSecrets(account_type="mock")
        settings = AppSettings.create(tmp_path, config, secrets)

        assert settings.environment == ENV_SIMULATION
        assert settings.is_simulation is True
        assert settings.is_mock_account is True

    def test_production_flags(self, tmp_path: Path) -> None:
        """Production settings expose correct flags."""
        config = _make_config(
            ENV_PRODUCTION,
            "https://openapi.koreainvestment.com:9443",
        )
        secrets = KisSecrets(account_type="real")
        settings = AppSettings.create(tmp_path, config, secrets)

        assert settings.is_production is True
        assert settings.is_real_account is True
        assert settings.uses_real_endpoint is True

    def test_resolve_path_relative(self, tmp_path: Path) -> None:
        """resolve_path resolves relative paths against project root."""
        config = _make_config(ENV_SIMULATION, KIS_VTS_REST_BASE_URL)
        settings = AppSettings.create(tmp_path, config, KisSecrets())

        resolved = settings.resolve_path("data/database/kats.db")

        assert resolved == tmp_path / "data/database/kats.db"

    def test_frozen_prevents_mutation(self, tmp_path: Path) -> None:
        """AppSettings is immutable."""
        config = _make_config(ENV_SIMULATION, KIS_VTS_REST_BASE_URL)
        settings = AppSettings.create(tmp_path, config, KisSecrets())

        with pytest.raises(AttributeError):
            settings.project_root = Path("/other")  # type: ignore[misc]
