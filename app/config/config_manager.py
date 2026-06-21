"""Singleton configuration manager for KATS."""

from __future__ import annotations

import logging
import shutil
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar

from pydantic import ValidationError

from app.config.app_settings import AppSettings
from app.config.config_loader import ConfigLoader, find_project_root, merge_configs
from app.config.config_models import KatsConfig
from app.config.config_validator import ConfigValidator
from app.config.env_loader import EnvironmentLoader
from app.config.exceptions import (
    ConfigLoadError,
    ConfigSaveError,
    ConfigValidationError,
    SecretValidationError,
)
from app.config.secret_manager import SecretManager
from app.core.constants import DOTENV_FILE_NAME, HOT_RELOAD_SECTIONS

logger = logging.getLogger(__name__)


class ConfigManager:
    """Thread-safe singleton configuration manager."""

    _instance: ClassVar[ConfigManager | None] = None
    _init_lock: ClassVar[threading.Lock] = threading.Lock()

    def __init__(
        self,
        project_root: Path | None = None,
        environment: str | None = None,
        json_loader: ConfigLoader | None = None,
        env_loader: EnvironmentLoader | None = None,
        secret_manager: SecretManager | None = None,
        validator: ConfigValidator | None = None,
    ) -> None:
        """Initialize ConfigManager. Use ``get_instance()`` instead of direct construction.

        Args:
            project_root: Project root directory.
            environment: Active environment name override.
            json_loader: Optional custom JSON config loader.
            env_loader: Optional custom environment loader.
            secret_manager: Optional custom secret manager.
            validator: Optional custom config validator.
        """
        self._lock = threading.RLock()
        self._project_root = project_root or find_project_root()
        self._environment_override = environment
        self._json_loader = json_loader or ConfigLoader(self._project_root)
        self._env_loader = env_loader or EnvironmentLoader()
        self._secret_manager = secret_manager or SecretManager()
        self._validator = validator or ConfigValidator()
        self._config: KatsConfig | None = None
        self._settings: AppSettings | None = None
        self._user_overrides: dict[str, Any] = {}

    @classmethod
    def get_instance(
        cls,
        project_root: Path | None = None,
        environment: str | None = None,
    ) -> ConfigManager:
        """Return the singleton ConfigManager instance.

        Args:
            project_root: Project root used on first initialization only.
            environment: Environment name used on first initialization only.

        Returns:
            Shared ConfigManager instance.
        """
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    cls._instance = cls(project_root=project_root, environment=environment)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance. Intended for testing only."""
        with cls._init_lock:
            cls._instance = None

    @property
    def project_root(self) -> Path:
        """Return the project root path."""
        return self._project_root

    @property
    def secret_manager(self) -> SecretManager:
        """Return the secret manager instance."""
        return self._secret_manager

    def load(self) -> AppSettings:
        """Load configuration from all sources and build ``AppSettings``.

        Load order (lowest to highest priority):
            JSON files → .env → OS environment variables → secrets injection

        Returns:
            Immutable ``AppSettings`` snapshot.

        Raises:
            ConfigLoadError: If configuration files cannot be loaded.
            ConfigValidationError: If validation fails critically.
            SecretValidationError: If required secrets are missing.
        """
        with self._lock:
            try:
                env_result = self._env_loader.load(
                    self._project_root / DOTENV_FILE_NAME,
                    self._environment_override,
                )
                json_config = self._json_loader.load_json_layers(env_result.environment)
                self._validator.validate_no_embedded_secrets(json_config)
                json_config = self._secret_manager.strip_json_auth_secrets(json_config)
                merged = merge_configs(json_config, env_result.to_nested_overrides())

                secrets = self._secret_manager.load_from_env(env_result.raw_env_vars)
                merged = self._secret_manager.apply_to_config_dict(merged)

                config = self._validator.validate_raw(merged)
                self._validator.validate_critical(config, secrets)

                try:
                    self._secret_manager.validate_for_environment(config.environment)
                except SecretValidationError as exc:
                    raise ConfigValidationError(str(exc)) from exc

                self._config = config
                self._settings = AppSettings.create(self._project_root, config, secrets)
                self._user_overrides = self._secret_manager.strip_from_config_dict(
                    self._json_loader.load_user_settings()
                )

                logger.info(
                    "Configuration loaded (env=%s, account_type=%s, kis_url=%s)",
                    config.environment,
                    secrets.account_type,
                    config.broker.base_url,
                )
                return self._settings
            except (ConfigValidationError, ConfigLoadError, SecretValidationError):
                raise
            except ValidationError as exc:
                msg = f"Configuration validation failed: {exc}"
                raise ConfigValidationError(msg) from exc
            except Exception as exc:
                msg = f"Unexpected error while loading configuration: {exc}"
                raise ConfigLoadError(msg) from exc

    def reload(self) -> AppSettings:
        """Reload configuration from disk and environment.

        Returns:
            Reloaded ``AppSettings`` snapshot.
        """
        with self._lock:
            logger.info("Reloading configuration")
            return self.load()

    def get_settings(self) -> AppSettings:
        """Return the current ``AppSettings`` snapshot.

        Returns:
            Immutable application settings.

        Raises:
            ConfigLoadError: If configuration has not been loaded yet.
        """
        with self._lock:
            if self._settings is None:
                return self.load()
            return AppSettings.create(
                self._settings.project_root,
                self._settings.config.model_copy(deep=True),
                self._settings.secrets,
            )

    def get(self) -> KatsConfig:
        """Return the current configuration model.

        Returns:
            Deep copy of the active ``KatsConfig``.

        Raises:
            ConfigLoadError: If configuration has not been loaded yet.
        """
        with self._lock:
            if self._config is None:
                self.load()
            assert self._config is not None
            return self._config.model_copy(deep=True)

    def get_value(self, key_path: str) -> Any:
        """Retrieve a configuration value using dot notation.

        Args:
            key_path: Dot-separated path (e.g. ``logging.level``).

        Returns:
            Configuration value at the given path.

        Raises:
            KeyError: If the path does not exist.
        """
        config = self.get()
        current: Any = config.model_dump()
        for key in key_path.split("."):
            if not isinstance(current, dict) or key not in current:
                msg = f"Configuration key not found: {key_path}"
                raise KeyError(msg)
            current = current[key]
        return current

    def set(self, key_path: str, value: Any) -> KatsConfig:
        """Update a runtime configuration value.

        Only hot-reloadable sections can be modified at runtime.

        Args:
            key_path: Dot-separated path (e.g. ``ui.theme``).
            value: New value to assign.

        Returns:
            Updated configuration model.

        Raises:
            ConfigValidationError: If the section is not hot-reloadable or value is invalid.
        """
        with self._lock:
            if self._config is None:
                self.load()

            section = key_path.split(".", maxsplit=1)[0]
            if section not in HOT_RELOAD_SECTIONS:
                msg = f"Section '{section}' cannot be modified at runtime"
                raise ConfigValidationError(msg)

            assert self._config is not None
            config_dict = self._config.model_dump()
            _set_nested_value(config_dict, key_path.split("."), value)

            try:
                updated = self._validator.validate_raw(config_dict)
            except ConfigValidationError as exc:
                msg = f"Invalid value for '{key_path}': {exc}"
                raise ConfigValidationError(msg) from exc

            self._config = updated
            if self._settings is not None:
                self._settings = AppSettings.create(
                    self._settings.project_root,
                    updated,
                    self._settings.secrets,
                )
            self._update_user_overrides(key_path.split("."), value)
            logger.info("Configuration updated: %s", key_path)
            return updated.model_copy(deep=True)

    def validate(self) -> bool:
        """Validate the currently loaded configuration.

        Returns:
            True if validation succeeds.

        Raises:
            ConfigValidationError: If validation fails.
        """
        with self._lock:
            if self._config is None or self._settings is None:
                self.load()
            assert self._config is not None
            assert self._settings is not None
            self._validator.validate_paths(self._config)
            self._validator.validate_kis_broker(self._config)
            self._validator.validate_critical(self._config, self._settings.secrets)
            return True

    def save(self) -> None:
        """Save user overrides to ``data/settings.json`` with backup.

        Secrets are stripped before persistence.

        Raises:
            ConfigSaveError: If settings cannot be saved.
        """
        with self._lock:
            if not self._user_overrides:
                self._user_overrides = self._secret_manager.strip_from_config_dict(
                    self._json_loader.load_user_settings()
                )

            sanitized = self._secret_manager.strip_from_config_dict(self._user_overrides)
            settings_path = self._json_loader.user_settings_path

            if (
                settings_path.exists()
                and self._config is not None
                and self._config.system.auto_backup
            ):
                self._backup_settings(settings_path)

            try:
                self._json_loader.save_user_settings(sanitized)
                self._user_overrides = sanitized
                logger.info("User settings saved to %s", settings_path)
            except OSError as exc:
                msg = f"Failed to save user settings: {exc}"
                raise ConfigSaveError(msg) from exc

    def _backup_settings(self, settings_path: Path) -> None:
        """Create a timestamped backup of the current settings file."""
        backup_dir = settings_path.parent / "backup"
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"settings_{timestamp}.json"
        shutil.copy2(settings_path, backup_path)
        logger.debug("Settings backup created: %s", backup_path)

    def _update_user_overrides(self, keys: list[str], value: Any) -> None:
        """Track user overrides for persistence."""
        current = self._user_overrides
        for key in keys[:-1]:
            nested = current.get(key)
            if not isinstance(nested, dict):
                nested = {}
                current[key] = nested
            current = nested
        current[keys[-1]] = value


def _set_nested_value(data: dict[str, Any], keys: list[str], value: Any) -> None:
    """Set a nested dictionary value."""
    current = data
    for key in keys[:-1]:
        nested = current.get(key)
        if not isinstance(nested, dict):
            nested = {}
            current[key] = nested
        current = nested
    current[keys[-1]] = value
