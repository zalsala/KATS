"""Authentication data models for KIS OpenAPI."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

KIS_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
KIS_TIMEZONE = ZoneInfo("Asia/Seoul")


@dataclass(frozen=True, slots=True)
class AccessToken:
    """KIS OAuth access token with expiry metadata.

    Attributes:
        token: Bearer access token string.
        expires_at: Token expiry instant in UTC.
        issued_at: Token issuance instant in UTC.
    """

    token: str
    expires_at: datetime
    issued_at: datetime

    def __post_init__(self) -> None:
        if not self.token:
            msg = "Access token value must not be empty"
            raise ValueError(msg)
        for field_name in ("expires_at", "issued_at"):
            value = getattr(self, field_name)
            if value.tzinfo is None:
                msg = f"{field_name} must be timezone-aware"
                raise ValueError(msg)

    def is_expired(
        self,
        *,
        now: datetime | None = None,
        margin_seconds: int = 0,
    ) -> bool:
        """Return True when the token is expired or within the refresh margin.

        Args:
            now: Reference time in UTC. Defaults to current UTC time.
            margin_seconds: Seconds before expiry to treat the token as expired.

        Returns:
            True if the token should be refreshed or reissued.
        """
        reference = now or datetime.now(UTC)
        effective_expiry = self.expires_at.timestamp() - margin_seconds
        return reference.timestamp() >= effective_expiry


@dataclass(frozen=True, slots=True)
class ApprovalKey:
    """KIS WebSocket approval key.

    Attributes:
        key: Approval key string returned by ``/oauth2/Approval``.
        issued_at: Issuance instant in UTC.
    """

    key: str
    issued_at: datetime

    def __post_init__(self) -> None:
        if not self.key:
            msg = "Approval key must not be empty"
            raise ValueError(msg)
        if self.issued_at.tzinfo is None:
            msg = "issued_at must be timezone-aware"
            raise ValueError(msg)


def parse_kis_expiry(expired_at: str) -> datetime:
    """Parse KIS ``access_token_token_expired`` into UTC datetime.

    Args:
        expired_at: KIS expiry timestamp string.

    Returns:
        Expiry instant in UTC.

    Raises:
        ValueError: If the expiry string format is invalid.
    """
    naive = datetime.strptime(expired_at, KIS_DATETIME_FORMAT)
    return naive.replace(tzinfo=KIS_TIMEZONE).astimezone(UTC)


def build_access_token(
    token: str,
    expired_at: str,
    *,
    issued_at: datetime | None = None,
) -> AccessToken:
    """Create an ``AccessToken`` from KIS OAuth response fields.

    Args:
        token: Access token string.
        expired_at: KIS ``access_token_token_expired`` value.
        issued_at: Optional issuance time. Defaults to current UTC time.

    Returns:
        Fully populated access token model.
    """
    issue_time = issued_at or datetime.now(UTC)
    if issue_time.tzinfo is None:
        msg = "issued_at must be timezone-aware"
        raise ValueError(msg)
    return AccessToken(
        token=token,
        expires_at=parse_kis_expiry(expired_at),
        issued_at=issue_time,
    )
