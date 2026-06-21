"""KIS OpenAPI secret management."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

from app.config.exceptions import SecretValidationError
from app.core.constants import (
    ENV_KIS_ACCOUNT_NO,
    ENV_KIS_ACCOUNT_TYPE,
    ENV_KIS_APP_KEY,
    ENV_KIS_APP_SECRET,
    ENV_PRODUCTION,
    KIS_ACCOUNT_MOCK,
    KIS_ACCOUNT_REAL,
    SECRET_ENV_KEYS,
    SECRET_MASK,
)

JSON_AUTH_SECRET_FIELDS: tuple[str, ...] = ("app_key", "app_secret", "account_no")

logger = logging.getLogger(__name__)

ACCOUNT_NO_PATTERN = re.compile(r"^\d{8,12}$")


@dataclass(frozen=True, slots=True)
class SecretSources:
    """Resolved sources for KIS credential fields."""

    app_key: str
    app_secret: str
    account_no: str

    def as_lines(self) -> tuple[str, str, str]:
        """Return credential source lines for CLI diagnostics."""
        return (
            f"APP_KEY source: {self.app_key}",
            f"APP_SECRET source: {self.app_secret}",
            f"ACCOUNT_NO source: {self.account_no}",
        )


@dataclass(frozen=True, slots=True)
class KisSecrets:
    """Immutable container for KIS OpenAPI credentials.

    Attributes:
        app_key: KIS application key.
        app_secret: KIS application secret.
        account_no: KIS account number (HTS ID).
        account_type: Account mode — ``mock`` (VTS) or ``real``.
    """

    app_key: str = ""
    app_secret: str = ""
    account_no: str = ""
    account_type: str = KIS_ACCOUNT_MOCK

    @property
    def is_configured(self) -> bool:
        """Return True when both app key and secret are present."""
        return bool(self.app_key and self.app_secret)

    @property
    def is_mock(self) -> bool:
        """Return True when account type is mock (VTS)."""
        return self.account_type == KIS_ACCOUNT_MOCK

    @property
    def is_real(self) -> bool:
        """Return True when account type is real."""
        return self.account_type == KIS_ACCOUNT_REAL


class SecretManager:
    """Manages KIS OpenAPI secrets separately from general configuration."""

    def __init__(self) -> None:
        """Initialize an empty secret manager."""
        self._secrets: KisSecrets = KisSecrets()

    @property
    def secrets(self) -> KisSecrets:
        """Return the currently loaded secrets."""
        return self._secrets

    def load_from_env(self, raw_env_vars: dict[str, str]) -> KisSecrets:
        """Load secrets from raw environment variable values.

        Args:
            raw_env_vars: Mapping of environment variable names to values.

        Returns:
            Loaded and validated ``KisSecrets`` instance.
        """
        account_type = raw_env_vars.get(ENV_KIS_ACCOUNT_TYPE, KIS_ACCOUNT_MOCK)
        if account_type not in (KIS_ACCOUNT_MOCK, KIS_ACCOUNT_REAL):
            logger.warning(
                "Invalid KIS_ACCOUNT_TYPE '%s', defaulting to '%s'",
                account_type,
                KIS_ACCOUNT_MOCK,
            )
            account_type = KIS_ACCOUNT_MOCK

        self._secrets = KisSecrets(
            app_key=raw_env_vars.get(ENV_KIS_APP_KEY, ""),
            app_secret=raw_env_vars.get(ENV_KIS_APP_SECRET, ""),
            account_no=raw_env_vars.get(ENV_KIS_ACCOUNT_NO, ""),
            account_type=account_type,
        )

        if self._secrets.is_configured:
            logger.info(
                "KIS secrets loaded (account_type=%s, account_no=%s)",
                self._secrets.account_type,
                self.mask(self._secrets.account_no) if self._secrets.account_no else "(empty)",
            )
        else:
            logger.warning("KIS API credentials not configured")

        return self._secrets

    @staticmethod
    def strip_json_auth_secrets(config_dict: dict[str, Any]) -> dict[str, Any]:
        """Remove JSON-configured auth secrets so only environment values are used."""
        result = _deep_copy_dict(config_dict)
        auth = result.get("authentication")
        if isinstance(auth, dict):
            for field in JSON_AUTH_SECRET_FIELDS:
                auth.pop(field, None)
        return result

    def apply_to_config_dict(self, config_dict: dict[str, Any]) -> dict[str, Any]:
        """Inject loaded secrets into a configuration dictionary.

        Args:
            config_dict: Merged configuration dictionary.

        Returns:
            Configuration dictionary with authentication secrets populated.
        """
        auth = config_dict.setdefault("authentication", {})
        auth["app_key"] = self._secrets.app_key
        auth["app_secret"] = self._secrets.app_secret
        auth["account_no"] = self._secrets.account_no
        auth["account_type"] = self._secrets.account_type
        return config_dict

    def strip_from_config_dict(self, config_dict: dict[str, Any]) -> dict[str, Any]:
        """Remove secrets from a configuration dictionary before persistence.

        Args:
            config_dict: Configuration dictionary potentially containing secrets.

        Returns:
            Sanitized copy safe for JSON persistence.
        """
        result = _deep_copy_dict(config_dict)
        auth = result.get("authentication")
        if isinstance(auth, dict):
            for field in JSON_AUTH_SECRET_FIELDS:
                auth.pop(field, None)
        return result

    def validate_for_environment(self, environment: str) -> None:
        """Validate that required secrets are present for the given environment.

        Args:
            environment: Active runtime environment name.

        Raises:
            SecretValidationError: If required secrets are missing.
        """
        if environment != ENV_PRODUCTION:
            return

        missing: list[str] = []
        if not self._secrets.app_key:
            missing.append(ENV_KIS_APP_KEY)
        if not self._secrets.app_secret:
            missing.append(ENV_KIS_APP_SECRET)

        if missing:
            msg = f"Missing required production secrets: {', '.join(missing)}"
            logger.error(msg)
            raise SecretValidationError(msg)

        if self._secrets.account_no and not ACCOUNT_NO_PATTERN.match(self._secrets.account_no):
            msg = "Invalid KIS account number format"
            logger.error(msg)
            raise SecretValidationError(msg)

    @staticmethod
    def mask(value: str, visible_chars: int = 4) -> str:
        """Mask a secret value for safe logging.

        Args:
            value: Secret string to mask.
            visible_chars: Number of characters to leave visible at the end.

        Returns:
            Masked string or empty string when input is empty.
        """
        if not value:
            return ""
        if len(value) <= visible_chars:
            return SECRET_MASK
        return f"{SECRET_MASK}{value[-visible_chars:]}"

    @staticmethod
    def is_secret_env_key(key: str) -> bool:
        """Return True if the environment variable key holds a secret value."""
        return key in SECRET_ENV_KEYS


def _deep_copy_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Create a shallow-deep copy of a nested dictionary."""
    result: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, dict):
            result[key] = _deep_copy_dict(value)
        else:
            result[key] = value
    return result
