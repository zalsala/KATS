"""Error mapper for KIS REST responses."""

from __future__ import annotations

from app.broker.kis.exceptions.auth_exceptions import AuthenticationError
from app.broker.kis.exceptions.rest_exceptions import (
    AuthorizationError,
    BrokerApiError,
    BrokerServerError,
    BrokerTimeoutError,
    NetworkError,
    RateLimitError,
    ResourceNotFoundError,
)
from app.broker.kis.rest.api_result import ApiResult
from app.broker.kis.rest.retry_policy import KIS_RATE_LIMIT_MSG_CODE

HTTP_STATUS_AUTHENTICATION = 401
HTTP_STATUS_AUTHORIZATION = 403
HTTP_STATUS_NOT_FOUND = 404
HTTP_STATUS_RATE_LIMIT = 429


class ErrorMapper:
    """Maps HTTP and KIS API errors to broker exceptions."""

    def map_http_status(self, status_code: int, *, msg1: str = "") -> Exception:
        """Map an HTTP status code to a broker exception.

        Args:
            status_code: HTTP status code.
            msg1: Optional KIS or HTTP message text.

        Returns:
            Mapped exception instance.
        """
        message = msg1 or f"HTTP error {status_code}"
        if status_code == HTTP_STATUS_AUTHENTICATION:
            return AuthenticationError(message)
        if status_code == HTTP_STATUS_AUTHORIZATION:
            return AuthorizationError(message)
        if status_code == HTTP_STATUS_NOT_FOUND:
            return ResourceNotFoundError(message)
        if status_code == HTTP_STATUS_RATE_LIMIT:
            return RateLimitError(message)
        if status_code >= 500:
            return BrokerServerError(message)
        return BrokerApiError(message, status_code=status_code)

    def map_api_result(self, result: ApiResult) -> Exception:
        """Map a failed ``ApiResult`` to a broker exception.

        Args:
            result: Parsed API result.

        Returns:
            Mapped exception instance.
        """
        if result.status_code != 200:
            return self.map_http_status(result.status_code, msg1=result.msg1)

        if result.msg_cd == KIS_RATE_LIMIT_MSG_CODE:
            return RateLimitError(result.msg1 or "KIS rate limit exceeded")

        return BrokerApiError(
            result.msg1 or "KIS API request failed",
            rt_cd=result.rt_cd,
            msg_cd=result.msg_cd,
            msg1=result.msg1,
            status_code=result.status_code,
        )

    def raise_for_result(self, result: ApiResult) -> ApiResult:
        """Return the result when successful or raise a mapped exception.

        Args:
            result: Parsed API result.

        Returns:
            The same result when successful.

        Raises:
            Exception: Mapped broker exception when the result failed.
        """
        if result.success:
            return result
        raise self.map_api_result(result) from None

    def map_transport_error(self, error: Exception) -> Exception:
        """Normalize transport-layer exceptions.

        Args:
            error: Raised transport exception.

        Returns:
            Broker exception instance.
        """
        if isinstance(
            error,
            (
                AuthenticationError,
                AuthorizationError,
                BrokerApiError,
                BrokerServerError,
                BrokerTimeoutError,
                NetworkError,
                RateLimitError,
                ResourceNotFoundError,
            ),
        ):
            return error
        if isinstance(error, TimeoutError):
            return BrokerTimeoutError(str(error))
        return NetworkError(str(error))
