"""Unit tests for SecretManager."""

from __future__ import annotations

import pytest

from app.config.exceptions import SecretValidationError
from app.config.secret_manager import KisSecrets, SecretManager
from app.core.constants import (
    ENV_KIS_ACCOUNT_NO,
    ENV_KIS_ACCOUNT_TYPE,
    ENV_KIS_APP_KEY,
    ENV_KIS_APP_SECRET,
    ENV_PRODUCTION,
    KIS_ACCOUNT_MOCK,
    KIS_ACCOUNT_REAL,
    SECRET_MASK,
)

pytestmark = pytest.mark.unit


class TestKisSecrets:
    """Tests for KisSecrets dataclass."""

    def test_is_configured_when_key_and_secret_present(self) -> None:
        """is_configured is True when app key and secret are set."""
        secrets = KisSecrets(app_key="key", app_secret="secret")

        assert secrets.is_configured is True

    def test_is_not_configured_when_empty(self) -> None:
        """is_configured is False when credentials are missing."""
        secrets = KisSecrets()

        assert secrets.is_configured is False


class TestSecretManager:
    """Tests for SecretManager."""

    def test_load_from_env(self) -> None:
        """load_from_env populates KisSecrets from raw env vars."""
        manager = SecretManager()
        secrets = manager.load_from_env(
            {
                ENV_KIS_APP_KEY: "my-key",
                ENV_KIS_APP_SECRET: "my-secret",
                ENV_KIS_ACCOUNT_NO: "1234567890",
                ENV_KIS_ACCOUNT_TYPE: KIS_ACCOUNT_REAL,
            }
        )

        assert secrets.app_key == "my-key"
        assert secrets.app_secret == "my-secret"
        assert secrets.account_no == "1234567890"
        assert secrets.account_type == KIS_ACCOUNT_REAL

    def test_load_defaults_to_mock_account(self) -> None:
        """Missing account type defaults to mock."""
        manager = SecretManager()
        secrets = manager.load_from_env({})

        assert secrets.account_type == KIS_ACCOUNT_MOCK

    def test_mask_short_value(self) -> None:
        """mask() fully masks short secret values."""
        assert SecretManager.mask("abc") == SECRET_MASK

    def test_mask_long_value_shows_suffix(self) -> None:
        """mask() shows last four characters of long values."""
        masked = SecretManager.mask("abcdefghijklmnop")

        assert masked.endswith("mnop")
        assert SECRET_MASK in masked

    def test_strip_from_config_dict(self) -> None:
        """strip_from_config_dict removes secrets before persistence."""
        manager = SecretManager()
        manager.load_from_env({ENV_KIS_APP_KEY: "key", ENV_KIS_APP_SECRET: "secret"})

        data = manager.apply_to_config_dict({"authentication": {}})
        stripped = manager.strip_from_config_dict(data)

        assert "app_key" not in stripped["authentication"]
        assert "app_secret" not in stripped["authentication"]

    def test_strip_json_auth_secrets(self) -> None:
        """JSON auth secrets are removed before environment injection."""
        config = {
            "authentication": {
                "app_key": "json-key",
                "app_secret": "json-secret",
                "account_no": "1234567890",
                "account_type": "mock",
            }
        }

        stripped = SecretManager.strip_json_auth_secrets(config)

        assert "app_key" not in stripped["authentication"]
        assert "app_secret" not in stripped["authentication"]
        assert "account_no" not in stripped["authentication"]
        assert stripped["authentication"]["account_type"] == "mock"

    def test_validate_production_requires_credentials(self) -> None:
        """Production validation fails without credentials."""
        manager = SecretManager()
        manager.load_from_env({})

        with pytest.raises(SecretValidationError, match="KIS_APP_KEY"):
            manager.validate_for_environment(ENV_PRODUCTION)

    def test_validate_production_passes_with_credentials(self) -> None:
        """Production validation passes when credentials are present."""
        manager = SecretManager()
        manager.load_from_env(
            {
                ENV_KIS_APP_KEY: "key",
                ENV_KIS_APP_SECRET: "secret",
            }
        )

        manager.validate_for_environment(ENV_PRODUCTION)

    def test_is_secret_env_key(self) -> None:
        """is_secret_env_key identifies secret environment keys."""
        assert SecretManager.is_secret_env_key(ENV_KIS_APP_KEY) is True
        assert SecretManager.is_secret_env_key("KATS_ENV") is False
