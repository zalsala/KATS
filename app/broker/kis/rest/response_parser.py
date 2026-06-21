"""REST response parser for KIS OpenAPI."""

from __future__ import annotations

from typing import Any

from app.broker.kis.rest.api_result import ApiResult
from app.broker.kis.rest.http_transport import RestHttpResponse

KIS_SUCCESS_RT_CD = "0"


class ResponseParser:
    """Parses KIS REST HTTP responses into ``ApiResult`` objects."""

    def parse(
        self,
        response: RestHttpResponse,
        *,
        method: str,
        path: str,
        tr_id: str | None,
        latency_ms: float,
    ) -> ApiResult:
        """Parse a transport response into a normalized API result.

        Args:
            response: Raw HTTP response from transport.
            method: HTTP method used for the request.
            path: Request API path.
            tr_id: KIS transaction ID when available.
            latency_ms: Request latency in milliseconds.

        Returns:
            Normalized ``ApiResult`` instance.
        """
        body = response.body
        rt_cd = _string_field(body, "rt_cd")
        msg_cd = _string_field(body, "msg_cd")
        msg1 = _string_field(body, "msg1")
        success = response.status_code == 200 and rt_cd == KIS_SUCCESS_RT_CD
        return ApiResult(
            success=success,
            status_code=response.status_code,
            data=body,
            rt_cd=rt_cd,
            msg_cd=msg_cd,
            msg1=msg1,
            latency_ms=latency_ms,
            tr_id=tr_id,
            path=path,
            method=method.upper(),
        )


def _string_field(body: dict[str, Any], key: str) -> str:
    value = body.get(key)
    if value is None:
        return ""
    return str(value)
