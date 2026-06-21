"""Unit tests for sensitive data masking."""

from __future__ import annotations

import pytest

from app.core.constants import SECRET_MASK
from app.core.logging.masker import SensitiveDataMasker

pytestmark = pytest.mark.unit


class TestSensitiveDataMasker:
    """Tests for SensitiveDataMasker."""

    @pytest.fixture
    def masker(self) -> SensitiveDataMasker:
        """Return a masker instance."""
        return SensitiveDataMasker()

    def test_mask_account_number(self, masker: SensitiveDataMasker) -> None:
        """Account numbers are masked in log messages."""
        message = "Account 12345678901 balance updated"

        masked = masker.mask(message)

        assert "12345678901" not in masked
        assert SECRET_MASK in masked

    def test_mask_bearer_token(self, masker: SensitiveDataMasker) -> None:
        """Bearer tokens are masked."""
        message = "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.token"

        masked = masker.mask(message)

        assert "eyJhbGciOiJIUzI1NiJ9" not in masked
        assert SECRET_MASK in masked

    def test_mask_key_value_secret(self, masker: SensitiveDataMasker) -> None:
        """Key=value secret patterns are masked."""
        message = "app_key=MY_SECRET_KEY_VALUE"

        masked = masker.mask(message)

        assert "MY_SECRET_KEY_VALUE" not in masked

    def test_mask_json_secret(self, masker: SensitiveDataMasker) -> None:
        """JSON-style secrets are masked."""
        message = '{"app_secret": "super-secret-value"}'

        masked = masker.mask(message)

        assert "super-secret-value" not in masked

    def test_mask_value_shows_suffix(self, masker: SensitiveDataMasker) -> None:
        """mask_value preserves trailing characters."""
        masked = masker.mask_value("abcdefghijklmnop")

        assert masked.endswith("mnop")
        assert SECRET_MASK in masked

    def test_empty_message_unchanged(self, masker: SensitiveDataMasker) -> None:
        """Empty messages pass through unchanged."""
        assert masker.mask("") == ""
