"""JSON configuration file loader."""

from __future__ import annotations

import json
import logging
from copy import deepcopy
from pathlib import Path
from typing import Any

from app.config.exceptions import ConfigLoadError
from app.core.constants import (
    CONFIG_DEFAULT_FILE,
    CONFIG_DIR_NAME,
    DATA_DIR_NAME,
    SETTINGS_FILE_NAME,
)

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Loads and merges JSON configuration files."""

    def __init__(self, project_root: Path) -> None:
        """Initialize the loader with the project root directory.

        Args:
            project_root: Root directory containing ``config/`` and ``data/`` folders.
        """
        self._project_root = project_root
        self._config_dir = project_root / CONFIG_DIR_NAME
        self._user_settings_path = project_root / DATA_DIR_NAME / SETTINGS_FILE_NAME

    @property
    def project_root(self) -> Path:
        """Return the project root path."""
        return self._project_root

    @property
    def user_settings_path(self) -> Path:
        """Return the user settings file path."""
        return self._user_settings_path

    def load_json_layers(self, environment: str) -> dict[str, Any]:
        """Load and merge JSON configuration layers.

        Merge priority (lowest to highest):
            ``default.json`` → ``{environment}.json`` → ``data/settings.json``

        Args:
            environment: Target environment name.

        Returns:
            Merged JSON configuration dictionary.

        Raises:
            ConfigLoadError: If ``default.json`` cannot be loaded.
        """
        merged = self._load_json_file(self._config_dir / CONFIG_DEFAULT_FILE, required=True)

        env_file = self._config_dir / f"{environment}.json"
        if env_file.exists():
            merged = _deep_merge(merged, self._load_json_file(env_file))
            logger.debug("Applied environment config: %s", env_file.name)
        else:
            logger.warning("Environment config not found: %s", env_file)

        if self._user_settings_path.exists():
            merged = _deep_merge(merged, self._load_json_file(self._user_settings_path))
            logger.debug("Applied user settings: %s", self._user_settings_path)

        return merged

    def save_user_settings(self, settings: dict[str, Any]) -> None:
        """Persist user settings to ``data/settings.json``.

        Args:
            settings: User settings dictionary to save.
        """
        self._user_settings_path.parent.mkdir(parents=True, exist_ok=True)
        with self._user_settings_path.open("w", encoding="utf-8") as file:
            json.dump(settings, file, indent=2, ensure_ascii=False)
        logger.info("User settings saved to %s", self._user_settings_path)

    def load_user_settings(self) -> dict[str, Any]:
        """Load existing user settings if present.

        Returns:
            User settings dictionary or empty dict.
        """
        if not self._user_settings_path.exists():
            return {}
        return self._load_json_file(self._user_settings_path)

    def _load_json_file(self, path: Path, required: bool = False) -> dict[str, Any]:
        """Load a JSON configuration file.

        Args:
            path: Path to the JSON file.
            required: Whether the file must exist.

        Returns:
            Parsed JSON content.

        Raises:
            ConfigLoadError: If a required file is missing or invalid.
        """
        if not path.exists():
            if required:
                msg = f"Required configuration file not found: {path}"
                raise ConfigLoadError(msg)
            return {}

        try:
            with path.open(encoding="utf-8") as file:
                content = json.load(file)
        except json.JSONDecodeError as exc:
            msg = f"Invalid JSON in configuration file: {path}"
            raise ConfigLoadError(msg) from exc

        if not isinstance(content, dict):
            msg = f"Configuration file must contain a JSON object: {path}"
            raise ConfigLoadError(msg)
        return content


def find_project_root(start: Path | None = None) -> Path:
    """Locate the project root by searching for ``config/default.json``.

    Args:
        start: Starting path for the search. Defaults to this module's location.

    Returns:
        Project root directory.

    Raises:
        ConfigLoadError: If project root cannot be determined.
    """
    current = (start or Path(__file__)).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / CONFIG_DIR_NAME / CONFIG_DEFAULT_FILE).exists():
            return candidate
    msg = f"Project root not found. Expected {CONFIG_DIR_NAME}/{CONFIG_DEFAULT_FILE}."
    raise ConfigLoadError(msg)


def merge_configs(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge two configuration dictionaries.

    Args:
        base: Base configuration dictionary.
        overlay: Overlay dictionary with higher priority values.

    Returns:
        Merged configuration dictionary.
    """
    return _deep_merge(base, overlay)


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge overlay into base."""
    result = deepcopy(base)
    for key, value in overlay.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result
