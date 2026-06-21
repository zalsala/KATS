"""Risk rule violation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RiskViolation:
    """Single risk rule violation."""

    rule_code: str
    message: str
