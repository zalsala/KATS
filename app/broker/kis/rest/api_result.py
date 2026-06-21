"""API result wrapper for KIS REST responses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ApiResult:
    """Normalized wrapper for a KIS REST API response.

    Attributes:
        success: True when HTTP 200 and ``rt_cd == \"0\"``.
        status_code: HTTP status code.
        data: Parsed JSON response body.
        rt_cd: KIS result code from the response body.
        msg_cd: KIS message code from the response body.
        msg1: KIS message text from the response body.
        latency_ms: Request round-trip latency in milliseconds.
        tr_id: KIS transaction ID when available.
        path: Request API path.
        method: HTTP method used for the request.
    """

    success: bool
    status_code: int
    data: dict[str, Any]
    rt_cd: str
    msg_cd: str
    msg1: str
    latency_ms: float
    tr_id: str | None = None
    path: str = ""
    method: str = "GET"

    @property
    def output(self) -> dict[str, Any]:
        """Return the ``output`` section when present."""
        output = self.data.get("output")
        if isinstance(output, dict):
            return output
        return {}

    @property
    def output1(self) -> list[dict[str, Any]]:
        """Return the ``output1`` list when present."""
        output1 = self.data.get("output1")
        if isinstance(output1, list):
            return [item for item in output1 if isinstance(item, dict)]
        return []
