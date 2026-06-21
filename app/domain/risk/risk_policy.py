"""Risk policy configuration."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.config.config_models import RiskConfig


@dataclass(frozen=True, slots=True)
class RiskPolicy:
    """Configurable risk rule thresholds."""

    max_order_amount: Decimal
    max_order_quantity: Decimal
    max_position_count: int
    max_symbol_weight: Decimal
    daily_loss_limit: Decimal
    duplicate_order_block: bool
    emergency_stop: bool

    @classmethod
    def from_config(
        cls, config: RiskConfig, *, max_symbol_weight: Decimal | None = None
    ) -> RiskPolicy:
        """Build policy from application ``RiskConfig``."""
        return cls(
            max_order_amount=Decimal(str(config.max_order_amount)),
            max_order_quantity=Decimal(str(config.max_quantity)),
            max_position_count=config.position_limit,
            max_symbol_weight=max_symbol_weight or Decimal("0.30"),
            daily_loss_limit=Decimal(str(config.daily_loss_limit)),
            duplicate_order_block=config.duplicate_order_block,
            emergency_stop=config.emergency_stop,
        )

    @classmethod
    def default(cls) -> RiskPolicy:
        """Return default risk policy."""
        return cls.from_config(RiskConfig())
