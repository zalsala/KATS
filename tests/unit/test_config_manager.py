"""Unit tests for ConfigManager."""

from __future__ import annotations

import json
import shutil
import threading
from pathlib import Path

import pytest

from app.config.config_loader import ConfigLoader
from app.config.config_manager import ConfigManager
from app.config.exceptions import ConfigLoadError, ConfigValidationError

pytestmark = pytest.mark.unit


class TestConfigManagerLoad:
    """Tests for configuration loading."""

    def test_load_returns_app_settings(self, project_root: Path) -> None:
        """load() returns an AppSettings instance."""
        manager = ConfigManager.get_instance(project_root=project_root, environment="development")
        settings = manager.load()

        assert settings.config.application.name == "KATS"
        assert settings.environment == "development"
        assert settings.config.broker.broker_type == "kis"

    def test_development_overrides_applied(self, project_root: Path) -> None:
        """Development environment applies debug override."""
        manager = ConfigManager.get_instance(project_root=project_root, environment="development")
        settings = manager.load()

        assert settings.config.application.debug is True
        assert settings.config.logging.level == "DEBUG"

    def test_production_config_urls(
        self,
        project_root: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Production environment uses live API URLs."""
        monkeypatch.setenv("KIS_APP_KEY", "test-app-key")
        monkeypatch.setenv("KIS_APP_SECRET", "test-app-secret")
        monkeypatch.setenv("KIS_ACCOUNT_TYPE", "real")
        ConfigManager.reset_instance()

        manager = ConfigManager.get_instance(project_root=project_root, environment="production")
        settings = manager.load()

        assert settings.uses_real_endpoint is True
        assert settings.config.application.debug is False

    def test_production_requires_credentials(
        self,
        tmp_path: Path,
        project_root: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Production startup fails without API credentials."""
        shutil.copytree(project_root / "config", tmp_path / "config")
        monkeypatch.delenv("KIS_APP_KEY", raising=False)
        monkeypatch.delenv("KIS_APP_SECRET", raising=False)
        monkeypatch.setenv("KIS_ACCOUNT_TYPE", "real")
        ConfigManager.reset_instance()

        manager = ConfigManager.get_instance(project_root=tmp_path, environment="production")

        with pytest.raises(ConfigValidationError, match="KIS_APP_KEY"):
            manager.load()

    def test_production_rejects_mock_account_type(
        self,
        project_root: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Production rejects mock account type."""
        monkeypatch.setenv("KIS_APP_KEY", "key")
        monkeypatch.setenv("KIS_APP_SECRET", "secret")
        monkeypatch.setenv("KIS_ACCOUNT_TYPE", "mock")
        ConfigManager.reset_instance()

        manager = ConfigManager.get_instance(project_root=project_root, environment="production")

        with pytest.raises(ConfigValidationError, match="mock account"):
            manager.load()

    def test_singleton_returns_same_instance(self, project_root: Path) -> None:
        """ConfigManager returns the same singleton instance."""
        first = ConfigManager.get_instance(project_root=project_root)
        second = ConfigManager.get_instance()

        assert first is second


class TestConfigManagerAccess:
    """Tests for configuration access methods."""

    def test_get_settings_returns_snapshot(self, project_root: Path) -> None:
        """get_settings() returns an immutable settings snapshot."""
        manager = ConfigManager.get_instance(project_root=project_root, environment="development")
        manager.load()

        settings = manager.get_settings()
        assert settings.config.application.name == "KATS"

    def test_get_returns_kats_config(self, project_root: Path) -> None:
        """get() returns a deep copy of KatsConfig."""
        manager = ConfigManager.get_instance(project_root=project_root, environment="development")
        manager.load()

        config = manager.get()
        config.application.name = "MODIFIED"

        assert manager.get().application.name == "KATS"

    def test_get_value_by_path(self, project_root: Path) -> None:
        """get_value() retrieves nested configuration values."""
        manager = ConfigManager.get_instance(project_root=project_root, environment="development")
        manager.load()

        assert manager.get_value("logging.level") == "DEBUG"
        assert manager.get_value("broker.timeout.connect") == 5

    def test_get_value_missing_key_raises(self, project_root: Path) -> None:
        """get_value() raises KeyError for unknown paths."""
        manager = ConfigManager.get_instance(project_root=project_root, environment="development")
        manager.load()

        with pytest.raises(KeyError, match="unknown.section"):
            manager.get_value("unknown.section")


class TestConfigManagerRuntime:
    """Tests for runtime configuration updates."""

    def test_set_hot_reloadable_value(self, project_root: Path) -> None:
        """set() updates hot-reloadable configuration values."""
        manager = ConfigManager.get_instance(project_root=project_root, environment="development")
        manager.load()

        updated = manager.set("ui.theme", "light")

        assert updated.ui.theme == "light"
        assert manager.get().ui.theme == "light"

    def test_set_non_hot_reloadable_raises(self, project_root: Path) -> None:
        """set() rejects modifications to non-hot-reloadable sections."""
        manager = ConfigManager.get_instance(project_root=project_root, environment="development")
        manager.load()

        with pytest.raises(ConfigValidationError, match="broker"):
            manager.set("broker.base_url", "https://example.com")

    def test_set_invalid_value_raises(self, project_root: Path) -> None:
        """set() rejects invalid values."""
        manager = ConfigManager.get_instance(project_root=project_root, environment="development")
        manager.load()

        with pytest.raises(ConfigValidationError):
            manager.set("ui.theme", "invalid_theme")


class TestConfigManagerPersistence:
    """Tests for save and reload."""

    def test_save_strips_secrets(
        self,
        project_root: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """save() does not persist secrets to settings.json."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        settings_path = data_dir / "settings.json"

        loader = ConfigLoader(project_root)
        monkeypatch.setattr(loader, "_user_settings_path", settings_path)

        manager = ConfigManager(
            project_root=project_root,
            environment="development",
            json_loader=loader,
        )
        manager.load()
        manager.set("ui.theme", "light")
        manager.save()

        saved = json.loads(settings_path.read_text(encoding="utf-8"))
        assert saved["ui"]["theme"] == "light"
        assert "app_key" not in saved.get("authentication", {})

    def test_save_creates_backup(
        self,
        project_root: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """save() creates a backup when settings file already exists."""
        data_dir = tmp_path / "data"
        backup_dir = tmp_path / "data" / "backup"
        data_dir.mkdir()
        settings_path = data_dir / "settings.json"
        settings_path.write_text('{"ui": {"theme": "dark"}}', encoding="utf-8")

        loader = ConfigLoader(project_root)
        monkeypatch.setattr(loader, "_user_settings_path", settings_path)

        manager = ConfigManager(
            project_root=project_root,
            environment="development",
            json_loader=loader,
        )
        manager.load()
        manager.set("ui.theme", "light")
        manager.save()

        backups = list(backup_dir.glob("settings_*.json"))
        assert len(backups) == 1


class TestConfigManagerEnvironment:
    """Tests for environment variable overrides."""

    def test_env_var_overrides_json(
        self,
        project_root: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Environment variables override JSON configuration."""
        monkeypatch.setenv("KIS_APP_KEY", "test-app-key")
        monkeypatch.setenv("KIS_APP_SECRET", "test-app-secret")
        ConfigManager.reset_instance()

        manager = ConfigManager.get_instance(project_root=project_root, environment="development")
        settings = manager.load()

        assert settings.secrets.app_key == "test-app-key"
        assert settings.secrets.app_secret == "test-app-secret"

    def test_json_auth_secrets_are_ignored_when_env_is_set(
        self,
        tmp_path: Path,
        project_root: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Embedded JSON credentials must not override .env secrets."""
        shutil.copytree(project_root / "config", tmp_path / "config")
        settings_path = tmp_path / "data" / "settings.json"
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(
            json.dumps(
                {
                    "authentication": {
                        "app_key": "json-key",
                        "app_secret": "json-secret",
                        "account_no": "99999999",
                    }
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setenv("KIS_APP_KEY", "env-key")
        monkeypatch.setenv("KIS_APP_SECRET", "env-secret")
        monkeypatch.setenv("KIS_ACCOUNT_NO", "12345678")
        ConfigManager.reset_instance()

        manager = ConfigManager.get_instance(project_root=tmp_path, environment="development")
        settings = manager.load()

        assert settings.secrets.app_key == "env-key"
        assert settings.secrets.app_secret == "env-secret"
        assert settings.secrets.account_no == "12345678"
        assert settings.config.authentication.app_key == "env-key"
        assert settings.config.authentication.app_secret == "env-secret"
        assert settings.config.authentication.account_no == "12345678"


class TestConfigManagerThreadSafety:
    """Tests for thread-safe access."""

    def test_concurrent_get(self, project_root: Path) -> None:
        """Concurrent get() calls do not raise errors."""
        manager = ConfigManager.get_instance(project_root=project_root, environment="development")
        manager.load()
        errors: list[Exception] = []

        def read_config() -> None:
            try:
                for _ in range(50):
                    config = manager.get()
                    assert config.application.name == "KATS"
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=read_config) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert not errors


class TestConfigManagerValidation:
    """Tests for validation."""

    def test_validate_returns_true(self, project_root: Path) -> None:
        """validate() returns True for valid configuration."""
        manager = ConfigManager.get_instance(project_root=project_root, environment="development")
        manager.load()

        assert manager.validate() is True

    def test_reload_refreshes_config(self, project_root: Path) -> None:
        """reload() refreshes configuration from sources."""
        manager = ConfigManager.get_instance(project_root=project_root, environment="development")
        manager.load()

        reloaded = manager.reload()
        assert reloaded.config.application.name == "KATS"


class TestConfigLoader:
    """Tests for ConfigLoader."""

    def test_find_project_root(self, project_root: Path) -> None:
        """find_project_root locates config/default.json."""
        from app.config.config_loader import find_project_root

        assert find_project_root(project_root / "app" / "config") == project_root

    def test_missing_default_raises(self, tmp_path: Path) -> None:
        """Loading without default.json raises ConfigLoadError."""
        loader = ConfigLoader(tmp_path)

        with pytest.raises(ConfigLoadError, match="default.json"):
            loader.load_json_layers("development")
