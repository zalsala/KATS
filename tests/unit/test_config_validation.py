"""Unit tests for configuration validation."""

from __future__ import annotations

import pytest

from app.config.config_models import (
    ApplicationConfig,
    AuthenticationConfig,
    BrokerConfig,
    KatsConfig,
)
from app.config.config_validator import ConfigValidator
from app.config.exceptions import ConfigValidationError
from app.config.secret_manager import KisSecrets
from app.core.constants import ENV_PRODUCTION, KIS_REAL_REST_BASE_URL, KIS_VTS_REST_BASE_URL

pytestmark = pytest.mark.unit


def _base_config(
    environment: str,
    base_url: str,
    account_type: str = "mock",
) -> KatsConfig:
    """Build a KatsConfig for validation tests."""
    return KatsConfig(
        application=ApplicationConfig(),
        broker=BrokerConfig(
            base_url=base_url,
            websocket_url="ws://ops.koreainvestment.com:21000",
        ),
        authentication=AuthenticationConfig(account_type=account_type),  # type: ignore[arg-type]
        environment=environment,  # type: ignore[arg-type]
    )


class TestConfigValidator:
    """Tests for ConfigValidator."""

    def test_validate_simulation_vts_url(self) -> None:
        """Simulation config with VTS URL passes KIS broker validation."""
        validator = ConfigValidator()
        config = _base_config("simulation", KIS_VTS_REST_BASE_URL)

        validator.validate_kis_broker(config)

    def test_validate_production_requires_real_url(self) -> None:
        """Production config must use real KIS REST URL."""
        validator = ConfigValidator()
        config = _base_config(ENV_PRODUCTION, KIS_VTS_REST_BASE_URL, account_type="real")

        with pytest.raises(ConfigValidationError, match="real REST URL"):
            validator.validate_kis_broker(config)

    def test_validate_production_rejects_mock_account(self) -> None:
        """Production config rejects mock account type."""
        validator = ConfigValidator()
        config = _base_config(ENV_PRODUCTION, KIS_REAL_REST_BASE_URL, account_type="mock")

        with pytest.raises(ConfigValidationError, match="mock account"):
            validator.validate_kis_broker(config)

    def test_validate_critical_production_missing_secrets(self) -> None:
        """Production critical validation fails without secrets."""
        validator = ConfigValidator()
        config = _base_config(ENV_PRODUCTION, KIS_REAL_REST_BASE_URL, account_type="real")
        secrets = KisSecrets()

        with pytest.raises(ConfigValidationError, match="KIS_APP_KEY"):
            validator.validate_critical(config, secrets)

    def test_warns_on_embedded_secrets(self) -> None:
        """Validator detects secrets embedded in JSON config."""
        validator = ConfigValidator()
        raw = {
            "authentication": {"app_key": "embedded-key"},
            "broker": {
                "base_url": KIS_VTS_REST_BASE_URL,
                "websocket_url": "ws://ops.koreainvestment.com:21000",
            },
        }

        validator.validate_no_embedded_secrets(raw)
