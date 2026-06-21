"""Sensitive data masking for safe log output."""

from __future__ import annotations

import re
from re import Pattern
from typing import Final

from app.core.constants import SECRET_MASK

# KIS account number: 8-12 digits
ACCOUNT_NO_PATTERN: Final[Pattern[str]] = re.compile(r"\b\d{8,12}\b")

# Bearer / access tokens
BEARER_TOKEN_PATTERN: Final[Pattern[str]] = re.compile(
    r"(Bearer\s+)[A-Za-z0-9\-._~+/]+=*",
    re.IGNORECASE,
)

# Generic key=value or key:value secret patterns
KEY_VALUE_SECRET_PATTERN: Final[Pattern[str]] = re.compile(
    r"(?i)(app[_-]?key|app[_-]?secret|access[_-]?token|approval[_-]?key|"
    r"hash[_-]?key|authorization|password|account[_-]?no)\s*[:=]\s*"
    r"([^\s,;'\"]+)",
)

# JSON-style quoted secrets
JSON_SECRET_PATTERN: Final[Pattern[str]] = re.compile(
    r'(?i)("(?:app_key|app_secret|access_token|approval_key|hash_key|'
    r'account_no|authorization)"\s*:\s*")([^"]+)(")',
)


class SensitiveDataMasker:
    """Masks sensitive values before they are written to logs."""

    def mask(self, message: str) -> str:
        """Mask all known sensitive patterns in a log message.

        Args:
            message: Raw log message text.

        Returns:
            Message with sensitive values replaced by ``****``.
        """
        if not message:
            return message

        masked = message
        masked = BEARER_TOKEN_PATTERN.sub(rf"\1{SECRET_MASK}", masked)
        masked = KEY_VALUE_SECRET_PATTERN.sub(
            lambda match: f"{match.group(1)}={SECRET_MASK}",
            masked,
        )
        masked = JSON_SECRET_PATTERN.sub(
            lambda match: f"{match.group(1)}{SECRET_MASK}{match.group(3)}",
            masked,
        )
        masked = self._mask_account_numbers(masked)
        return masked

    def mask_value(self, value: str, visible_chars: int = 4) -> str:
        """Mask a single secret value for structured logging.

        Args:
            value: Secret string to mask.
            visible_chars: Number of trailing characters to preserve.

        Returns:
            Masked string.
        """
        if not value:
            return ""
        if len(value) <= visible_chars:
            return SECRET_MASK
        return f"{SECRET_MASK}{value[-visible_chars:]}"

    @staticmethod
    def _mask_account_numbers(message: str) -> str:
        """Mask numeric sequences that resemble KIS account numbers."""
        return ACCOUNT_NO_PATTERN.sub(SECRET_MASK, message)
