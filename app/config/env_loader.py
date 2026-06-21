"""Environment and .env configuration loader."""

from __future__ import annotations

import logging
import os
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dotenv import dotenv_values

from app.config.secret_manager import SecretSources
from app.core.constants import (
    ENV_DEVELOPMENT,
    ENV_KATS_ENV,
    ENV_KIS_ACCOUNT_NO,
    ENV_KIS_ACCOUNT_TYPE,
    ENV_KIS_APP_KEY,
    ENV_KIS_APP_SECRET,
    SUPPORTED_ENVIRONMENTS,
)

DEFAULT_ENVIRONMENT = ENV_DEVELOPMENT

logger = logging.getLogger(__name__)

ENV_VAR_MAPPINGS: dict[str, tuple[str, ...]] = {
    ENV_KIS_APP_KEY: ("authentication", "app_key"),
    ENV_KIS_APP_SECRET: ("authentication", "app_secret"),
    ENV_KIS_ACCOUNT_NO: ("authentication", "account_no"),
    ENV_KIS_ACCOUNT_TYPE: ("authentication", "account_type"),
}


@dataclass(frozen=True, slots=True)
class EnvironmentLoadResult:
    """Result of loading environment configuration sources.

    Attributes:
        environment: Resolved environment name.
        dotenv_path: Path to the loaded .env file, if any.
        dotenv_values: Key-value pairs read from the .env file.
        env_overrides: Nested configuration overrides from environment variables.
        raw_env_vars: Raw OS environment variable values for secret keys.
    """

    environment: str
    dotenv_path: Path | None
    dotenv_values: dict[str, str | None] = field(default_factory=dict)
    env_overrides: dict[str, Any] = field(default_factory=dict)
    raw_env_vars: dict[str, str] = field(default_factory=dict)

    def to_nested_overrides(self) -> dict[str, Any]:
        """Return merged nested overrides from .env and environment variables.

        Priority (lowest to highest): .env file values, then OS environment
        variables. This matches the specification order where environment
        variables override .env values.

        Returns:
            Nested dictionary suitable for merging into JSON configuration.
        """
        merged: dict[str, Any] = {}
        dotenv_nested = _flat_to_nested(self.dotenv_values)
        merged = _deep_merge(merged, dotenv_nested)
        merged = _deep_merge(merged, self.env_overrides)
        merged["environment"] = self.environment
        return merged

    def secret_sources(self) -> SecretSources:
        """Return whether each credential came from environment sources."""

        def resolve(env_key: str) -> str:
            if os.getenv(env_key):
                return "env"
            dotenv_value = self.dotenv_values.get(env_key)
            if dotenv_value:
                return "env"
            return "missing"

        return SecretSources(
            app_key=resolve(ENV_KIS_APP_KEY),
            app_secret=resolve(ENV_KIS_APP_SECRET),
            account_no=resolve(ENV_KIS_ACCOUNT_NO),
        )


class EnvironmentLoader:
    """Loads configuration from .env files and OS environment variables."""

    def load(
        self,
        dotenv_path: Path,
        environment: str | None = None,
    ) -> EnvironmentLoadResult:
        """Load environment configuration.

        Args:
            dotenv_path: Path to the ``.env`` file.
            environment: Explicit environment override. Falls back to
                ``KATS_ENV`` from OS environment or .env file.

        Returns:
            Structured result containing resolved environment and overrides.
        """
        dotenv_data: dict[str, str | None] = {}
        resolved_dotenv_path: Path | None = None

        if dotenv_path.exists():
            dotenv_data = dict(dotenv_values(dotenv_path))
            resolved_dotenv_path = dotenv_path
            logger.debug("Loaded .env from %s", dotenv_path)
        else:
            logger.debug(".env file not found at %s", dotenv_path)

        env_name = self._resolve_environment(environment, dotenv_data)
        dotenv_overrides = _flat_to_nested(dotenv_data)
        os_overrides = self._collect_os_env_overrides()

        combined_overrides = _deep_merge(dotenv_overrides, os_overrides)
        combined_overrides["environment"] = env_name

        raw_secrets = self._collect_raw_secret_values(dotenv_data)

        logger.info("Environment resolved: %s", env_name)
        return EnvironmentLoadResult(
            environment=env_name,
            dotenv_path=resolved_dotenv_path,
            dotenv_values=dotenv_data,
            env_overrides=combined_overrides,
            raw_env_vars=raw_secrets,
        )

    def _resolve_environment(
        self,
        explicit: str | None,
        dotenv_data: dict[str, str | None],
    ) -> str:
        """Resolve the active environment name.

        Priority: explicit argument > OS env > .env > default.
        """
        candidate = (
            explicit
            or os.getenv(ENV_KATS_ENV)
            or dotenv_data.get(ENV_KATS_ENV)
            or DEFAULT_ENVIRONMENT
        )
        if candidate not in SUPPORTED_ENVIRONMENTS:
            logger.warning(
                "Unknown environment '%s', falling back to %s",
                candidate,
                DEFAULT_ENVIRONMENT,
            )
            return DEFAULT_ENVIRONMENT
        return candidate

    def _collect_os_env_overrides(self) -> dict[str, Any]:
        """Collect configuration overrides from OS environment variables."""
        overrides: dict[str, Any] = {}
        for env_key, path in ENV_VAR_MAPPINGS.items():
            value = os.getenv(env_key)
            if value is not None:
                _set_nested(overrides, path, value)
        kats_env = os.getenv(ENV_KATS_ENV)
        if kats_env is not None:
            overrides["environment"] = kats_env
        return overrides

    @staticmethod
    def _collect_raw_secret_values(dotenv_data: dict[str, str | None]) -> dict[str, str]:
        """Collect raw secret values with OS environment taking priority over .env."""
        raw: dict[str, str] = {}
        for key in (ENV_KIS_APP_KEY, ENV_KIS_APP_SECRET, ENV_KIS_ACCOUNT_NO, ENV_KIS_ACCOUNT_TYPE):
            os_value = os.getenv(key)
            if os_value is not None:
                raw[key] = os_value
            elif dotenv_data.get(key):
                raw[key] = str(dotenv_data[key])
        return raw


def _flat_to_nested(flat: dict[str, str | None]) -> dict[str, Any]:
    """Convert flat environment entries to nested configuration structure."""
    nested: dict[str, Any] = {}
    for key, value in flat.items():
        if value is None or value == "":
            continue
        if key in ENV_VAR_MAPPINGS:
            _set_nested(nested, ENV_VAR_MAPPINGS[key], value)
        elif key == ENV_KATS_ENV:
            nested["environment"] = value
    return nested


def _set_nested(data: dict[str, Any], path: tuple[str, ...], value: Any) -> None:
    """Set a value in a nested dictionary using a key path."""
    current = data
    for key in path[:-1]:
        current = current.setdefault(key, {})
    current[path[-1]] = value


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge overlay into base."""
    result = deepcopy(base)
    for key, value in overlay.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result
