"""Error response DTO for KIS REST APIs."""

from __future__ import annotations

from pydantic import BaseModel


class ErrorResponseDto(BaseModel):
    """Normalized KIS REST error response.

    Attributes:
        rt_cd: KIS result code.
        msg_cd: KIS message code.
        msg1: KIS message text.
        status_code: HTTP status code when available.
        tr_id: Related TR ID when available.
    """

    rt_cd: str
    msg_cd: str = ""
    msg1: str = ""
    status_code: int = 200
    tr_id: str | None = None

    @property
    def is_success(self) -> bool:
        """Return True when the error DTO represents success."""
        return self.rt_cd == "0" and self.status_code == 200

    @classmethod
    def from_dict(
        cls,
        data: dict[str, object],
        *,
        status_code: int = 200,
        tr_id: str | None = None,
    ) -> ErrorResponseDto:
        """Build an error DTO from a parsed response body.

        Args:
            data: Parsed JSON response body.
            status_code: HTTP status code.
            tr_id: Related TR ID.

        Returns:
            Normalized error response DTO.
        """
        return cls(
            rt_cd=str(data.get("rt_cd", "")),
            msg_cd=str(data.get("msg_cd", "")),
            msg1=str(data.get("msg1", "")),
            status_code=status_code,
            tr_id=tr_id,
        )

    def to_message(self) -> str:
        """Return a human-readable error message."""
        if self.msg1:
            return self.msg1
        if self.msg_cd:
            return f"KIS error {self.msg_cd}"
        return f"HTTP error {self.status_code}"
