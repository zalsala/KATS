"""Risk policy repository interface."""

from __future__ import annotations

from typing import Protocol

from app.domain.risk.risk_policy import RiskPolicy


class RiskPolicyRepository(Protocol):
    """Persistence contract for risk policies."""

    def save(self, policy: RiskPolicy, *, policy_name: str = "default") -> None:
        """Persist a risk policy."""

    def get(self, policy_name: str = "default") -> RiskPolicy | None:
        """Load a risk policy by name."""

    def list_all(self) -> list[tuple[str, RiskPolicy]]:
        """Return all stored risk policies."""
