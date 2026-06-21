"""Unit tests for ErrorMapper."""

from __future__ import annotations

import pytest

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
from app.broker.kis.rest.error_mapper import ErrorMapper

pytestmark = pytest.mark.unit


def _result(
    *,
    success: bool = False,
    status_code: int = 200,
    rt_cd: str = "1",
    msg_cd: str = "ERR",
    msg1: str = "failed",
) -> ApiResult:
    return ApiResult(
        success=success,
        status_code=status_code,
        data={"rt_cd": rt_cd, "msg_cd": msg_cd, "msg1": msg1},
        rt_cd=rt_cd,
        msg_cd=msg_cd,
        msg1=msg1,
        latency_ms=1.0,
    )


class TestErrorMapper:
    """Tests for ErrorMapper."""

    def test_map_http_401(self) -> None:
        """HTTP 401 maps to AuthenticationError."""
        error = ErrorMapper().map_http_status(401)

        assert isinstance(error, AuthenticationError)

    def test_map_http_403(self) -> None:
        """HTTP 403 maps to AuthorizationError."""
        error = ErrorMapper().map_http_status(403)

        assert isinstance(error, AuthorizationError)

    def test_map_http_404(self) -> None:
        """HTTP 404 maps to ResourceNotFoundError."""
        error = ErrorMapper().map_http_status(404)

        assert isinstance(error, ResourceNotFoundError)

    def test_map_http_429(self) -> None:
        """HTTP 429 maps to RateLimitError."""
        error = ErrorMapper().map_http_status(429)

        assert isinstance(error, RateLimitError)

    def test_map_http_500(self) -> None:
        """HTTP 500 maps to BrokerServerError."""
        error = ErrorMapper().map_http_status(500)

        assert isinstance(error, BrokerServerError)

    def test_map_api_result_rt_cd_failure(self) -> None:
        """rt_cd != 0 maps to BrokerApiError."""
        error = ErrorMapper().map_api_result(_result())

        assert isinstance(error, BrokerApiError)
        assert error.rt_cd == "1"
        assert error.msg_cd == "ERR"

    def test_map_api_result_kis_rate_limit_code(self) -> None:
        """EGW00201 maps to RateLimitError."""
        error = ErrorMapper().map_api_result(_result(msg_cd="EGW00201", msg1="rate limit"))

        assert isinstance(error, RateLimitError)

    def test_raise_for_result_success(self) -> None:
        """Successful result is returned unchanged."""
        result = _result(success=True, rt_cd="0", msg_cd="MCA00000", msg1="ok")

        returned = ErrorMapper().raise_for_result(result)

        assert returned is result

    def test_raise_for_result_failure(self) -> None:
        """Failed result raises mapped exception."""
        with pytest.raises(BrokerApiError):
            ErrorMapper().raise_for_result(_result())

    def test_map_transport_timeout(self) -> None:
        """TimeoutError maps to BrokerTimeoutError."""
        mapped = ErrorMapper().map_transport_error(TimeoutError("timed out"))

        assert isinstance(mapped, BrokerTimeoutError)

    def test_map_transport_network(self) -> None:
        """NetworkError passes through unchanged."""
        original = NetworkError("offline")
        mapped = ErrorMapper().map_transport_error(original)

        assert mapped is original
