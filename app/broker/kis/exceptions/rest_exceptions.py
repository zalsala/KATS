"""REST client broker exceptions."""

from __future__ import annotations

from app.broker.kis.exceptions.auth_exceptions import AuthenticationError, BrokerError


class BrokerTimeoutError(BrokerError):
    """Raised when a REST request exceeds the configured timeout."""


class NetworkError(BrokerError):
    """Raised when a network-level failure occurs."""


class RateLimitError(BrokerError):
    """Raised when KIS rate limits are exceeded."""


class AuthorizationError(BrokerError):
    """Raised when access is forbidden."""


class ResourceNotFoundError(BrokerError):
    """Raised when the requested KIS resource is not found."""


class BrokerServerError(BrokerError):
    """Raised when KIS returns a server-side error."""


class BrokerApiError(BrokerError):
    """Raised when KIS returns ``rt_cd != \"0\"``."""

    def __init__(
        self,
        message: str,
        *,
        rt_cd: str = "",
        msg_cd: str = "",
        msg1: str = "",
        status_code: int = 200,
    ) -> None:
        """Initialize a KIS API business error.

        Args:
            message: Human-readable error message.
            rt_cd: KIS response result code.
            msg_cd: KIS message code.
            msg1: KIS message text.
            status_code: HTTP status code.
        """
        super().__init__(message)
        self.rt_cd = rt_cd
        self.msg_cd = msg_cd
        self.msg1 = msg1
        self.status_code = status_code


# Re-export auth error for mapper convenience
__all__ = [
    "AuthenticationError",
    "AuthorizationError",
    "BrokerApiError",
    "BrokerServerError",
    "BrokerTimeoutError",
    "NetworkError",
    "RateLimitError",
    "ResourceNotFoundError",
]
