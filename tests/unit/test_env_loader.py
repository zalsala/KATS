"""Unit tests for EnvironmentLoader."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.config.env_loader import EnvironmentLoader
from app.core.constants import ENV_DEVELOPMENT, ENV_KIS_APP_KEY

pytestmark = pytest.mark.unit


class TestEnvironmentLoader:
    """Tests for EnvironmentLoader."""

    def test_load_resolves_development_by_default(self, tmp_path: Path) -> None:
        """Default environment is development when no .env exists."""
        loader = EnvironmentLoader()
        result = loader.load(tmp_path / ".env")

        assert result.environment == ENV_DEVELOPMENT

    def test_load_reads_dotenv_file(self, tmp_path: Path) -> None:
        """Loader reads values from .env file."""
        dotenv = tmp_path / ".env"
        dotenv.write_text(f"{ENV_KIS_APP_KEY}=from-dotenv\nKATS_ENV=simulation\n", encoding="utf-8")

        loader = EnvironmentLoader()
        result = loader.load(dotenv)

        assert result.environment == "simulation"
        assert result.dotenv_values[ENV_KIS_APP_KEY] == "from-dotenv"

    def test_os_env_overrides_dotenv(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """OS environment variables override .env values."""
        dotenv = tmp_path / ".env"
        dotenv.write_text(f"{ENV_KIS_APP_KEY}=from-dotenv\n", encoding="utf-8")
        monkeypatch.setenv(ENV_KIS_APP_KEY, "from-os")

        loader = EnvironmentLoader()
        result = loader.load(dotenv)

        assert result.raw_env_vars[ENV_KIS_APP_KEY] == "from-os"
        nested = result.to_nested_overrides()
        assert nested["authentication"]["app_key"] == "from-os"

    def test_unknown_environment_falls_back(self, tmp_path: Path) -> None:
        """Unknown environment name falls back to development."""
        dotenv = tmp_path / ".env"
        dotenv.write_text("KATS_ENV=unknown_env\n", encoding="utf-8")

        loader = EnvironmentLoader()
        result = loader.load(dotenv)

        assert result.environment == ENV_DEVELOPMENT

    def test_secret_sources_from_dotenv(self, tmp_path: Path) -> None:
        """secret_sources reports env for credentials loaded from .env."""
        dotenv = tmp_path / ".env"
        dotenv.write_text(
            "KIS_APP_KEY=from-dotenv\nKIS_APP_SECRET=from-dotenv\nKIS_ACCOUNT_NO=12345678\n",
            encoding="utf-8",
        )

        result = EnvironmentLoader().load(dotenv)
        sources = result.secret_sources()

        assert sources.app_key == "env"
        assert sources.app_secret == "env"
        assert sources.account_no == "env"

    def test_secret_sources_missing_without_env(self, tmp_path: Path) -> None:
        """secret_sources reports missing when credentials are absent."""
        result = EnvironmentLoader().load(tmp_path / ".env")
        sources = result.secret_sources()

        assert sources.app_key == "missing"
        assert sources.app_secret == "missing"
        assert sources.account_no == "missing"
