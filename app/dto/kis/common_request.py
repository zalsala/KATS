"""Common KIS REST request DTO."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CommonRequestDto(BaseModel):
    """Standard KIS REST request envelope.

    Attributes:
        tr_id: KIS transaction ID sent in headers.
        custtype: Customer type header value.
        params: Query or body parameters keyed by official KIS field names.
        hashkey: Optional hash key for order requests.
        tr_cont: Optional pagination continuation flag.
    """

    tr_id: str
    custtype: str = "P"
    params: dict[str, Any] = Field(default_factory=dict)
    hashkey: str | None = None
    tr_cont: str | None = None

    def header_overrides(self) -> dict[str, str]:
        """Return optional header overrides derived from the request DTO."""
        headers: dict[str, str] = {"custtype": self.custtype}
        if self.hashkey:
            headers["hashkey"] = self.hashkey
        if self.tr_cont is not None:
            headers["tr_cont"] = self.tr_cont
        return headers
