"""Common KIS REST response DTO."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class CommonResponseDto(BaseModel):
    """Standard KIS REST response envelope.

    Attributes:
        rt_cd: KIS result code. ``0`` indicates success.
        msg_cd: KIS message code.
        msg1: KIS message text.
        output: Single-object response section.
        output1: List response section.
        output2: Secondary list response section.
    """

    rt_cd: str
    msg_cd: str = ""
    msg1: str = ""
    output: dict[str, Any] | None = None
    output1: list[dict[str, Any]] | None = None
    output2: list[dict[str, Any]] | None = None

    @property
    def is_success(self) -> bool:
        """Return True when ``rt_cd`` indicates success."""
        return self.rt_cd == "0"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CommonResponseDto:
        """Build a response DTO from a parsed JSON dictionary.

        Args:
            data: Parsed KIS REST response body.

        Returns:
            Normalized response DTO.
        """
        output = data.get("output")
        output1 = data.get("output1")
        output2 = data.get("output2")
        return cls(
            rt_cd=str(data.get("rt_cd", "")),
            msg_cd=str(data.get("msg_cd", "")),
            msg1=str(data.get("msg1", "")),
            output=output if isinstance(output, dict) else None,
            output1=output1 if isinstance(output1, list) else None,
            output2=output2 if isinstance(output2, list) else None,
        )

    def primary_output(self) -> dict[str, Any]:
        """Return the first available output object."""
        if self.output:
            return self.output
        if self.output1:
            return self.output1[0]
        return {}

    def all_rows(self) -> list[dict[str, Any]]:
        """Return all list rows from ``output1`` and ``output2``."""
        rows: list[dict[str, Any]] = []
        if self.output1:
            rows.extend(item for item in self.output1 if isinstance(item, dict))
        if self.output2:
            rows.extend(item for item in self.output2 if isinstance(item, dict))
        return rows
