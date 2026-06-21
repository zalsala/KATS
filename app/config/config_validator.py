"""Configuration validation logic."""

from __future__ import annotations

import logging
from pathlib import Path

from pydantic import ValidationError

from app.config.config_models import KatsConfig
from app.config.exceptions import ConfigValidationError
from app.config.secret_manager import KisSecrets, SecretManager
from app.core.constants import (
    ENV_PRODUCTION,
    ENV_SIMULATION,
    KIS_REAL_REST_BASE_URL,
    KIS_REAL_WS_URL,
    KIS_VTS_REST_BASE_URL,
    KIS_VTS_WS_URL,
)

logger = logging.getLogger(__name__)


class ConfigValidator:
    """Validates configuration data, paths, and KIS OpenAPI consistency."""

    def validate_raw(self, raw_config: dict[str, object]) -> KatsConfig:
        """Validate raw configuration and return a typed model.

        Args:
            raw_config: Merged configuration dictionary.

        Returns:
            Validated ``KatsConfig`` instance.

        Raises:
            ConfigValidationError: If Pydantic validation fails.
        """
        try:
            config = KatsConfig.model_validate(raw_config)
        except ValidationError as exc:
            msg = f"Configuration validation failed: {exc}"
            logger.error(msg)
            raise ConfigValidationError(msg) from exc

        self.validate_paths(config)
        self.validate_kis_broker(config)
        return config

    def validate_paths(self, config: KatsConfig) -> None:
        """Validate filesystem paths referenced in configuration.

        Args:
            config: Validated configuration model.

        Raises:
            ConfigValidationError: If a path parent cannot be created.
        """
        path_fields = [
            config.database.database_path,
            config.database.backup_path,
            config.authentication.token_path,
            config.strategy.plugin_path,
        ]
        for path_value in path_fields:
            path = Path(path_value)
            parent = path.parent if path.parent != Path(".") else Path("data")
            if path.is_absolute():
                parent = path.parent
            try:
                parent.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                msg = f"Cannot create directory for path '{path_value}': {exc}"
                logger.error(msg)
                raise ConfigValidationError(msg) from exc

    def validate_kis_broker(self, config: KatsConfig) -> None:
        """Validate KIS OpenAPI broker URL consistency with environment.

        Args:
            config: Validated configuration model.

        Raises:
            ConfigValidationError: If broker URLs do not match the environment.
        """
        env = config.environment
        base_url = config.broker.base_url
        ws_url = config.broker.websocket_url

        if env in (ENV_SIMULATION, "development"):
            if KIS_VTS_REST_BASE_URL not in base_url and env == ENV_SIMULATION:
                logger.warning(
                    "Simulation environment should use VTS REST URL: %s",
                    KIS_VTS_REST_BASE_URL,
                )
            expected_ws = KIS_VTS_WS_URL
            if ws_url and expected_ws not in ws_url:
                logger.debug("WebSocket URL differs from default VTS endpoint")

        if env == ENV_PRODUCTION:
            if KIS_REAL_REST_BASE_URL not in base_url:
                msg = (
                    f"Production environment must use KIS real REST URL: "
                    f"{KIS_REAL_REST_BASE_URL}"
                )
                logger.error(msg)
                raise ConfigValidationError(msg)
            if KIS_REAL_WS_URL not in ws_url:
                logger.warning(
                    "Production WebSocket URL may not match expected real endpoint: %s",
                    KIS_REAL_WS_URL,
                )

        account_type = config.authentication.account_type
        if env == ENV_PRODUCTION and account_type == "mock":
            msg = "Production environment cannot use mock account type"
            logger.error(msg)
            raise ConfigValidationError(msg)

        logger.debug(
            "KIS broker validation passed (env=%s, base_url=%s)",
            env,
            base_url,
        )

    def validate_no_embedded_secrets(self, raw_config: dict[str, object]) -> None:
        """Warn when secrets are embedded in JSON configuration files.

        Call this on JSON layers only (before environment secret injection).
        Secrets must come from environment variables or .env only.

        Args:
            raw_config: Raw merged configuration before secret injection.
        """
        auth = raw_config.get("authentication")
        if not isinstance(auth, dict):
            return

        for field in ("app_key", "app_secret", "account_no"):
            value = auth.get(field)
            if isinstance(value, str) and value:
                logger.warning(
                    "Secret '%s' found in JSON config — use environment variables instead",
                    field,
                )

    def validate_secrets(self, secrets: KisSecrets, environment: str) -> None:
        """Validate KIS secrets for the given environment.

        Args:
            secrets: Loaded KIS API secrets.
            environment: Active runtime environment.

        Raises:
            ConfigValidationError: If secrets are invalid for the environment.
        """
        manager = SecretManager()
        manager._secrets = secrets  # noqa: SLF001 — validation-only access
        try:
            manager.validate_for_environment(environment)
        except Exception as exc:
            if not isinstance(exc, ConfigValidationError):
                from app.config.exceptions import SecretValidationError

                if isinstance(exc, SecretValidationError):
                    raise ConfigValidationError(str(exc)) from exc
            raise

    def validate_critical(self, config: KatsConfig, secrets: KisSecrets) -> None:
        """Validate critical settings required for production startup.

        Args:
            config: Validated configuration model.
            secrets: Loaded KIS API secrets.

        Raises:
            ConfigValidationError: If critical production settings are missing.
        """
        if config.environment != ENV_PRODUCTION:
            return

        missing: list[str] = []
        if not secrets.app_key:
            missing.append("KIS_APP_KEY")
        if not secrets.app_secret:
            missing.append("KIS_APP_SECRET")

        if missing:
            msg = f"Missing required production credentials: {', '.join(missing)}"
            logger.error(msg)
            raise ConfigValidationError(msg)
