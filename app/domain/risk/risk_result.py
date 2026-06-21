"""Risk evaluation result."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.risk.risk_violation import RiskViolation


@dataclass(frozen=True, slots=True)
class RiskResult:
    """Outcome of risk validation for a trading signal."""

    approved: bool
    signal_id: str
    symbol_code: str
    signal_type: str
    violations: tuple[RiskViolation, ...]
    message: str

    @property
    def status(self) -> str:
        """Return APPROVED or REJECTED status string."""
        return "APPROVED" if self.approved else "REJECTED"
