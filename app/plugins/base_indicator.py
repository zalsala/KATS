"""Base indicator interface for plugin indicators."""

from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any


class BaseIndicator(ABC):
    """Abstract base class for indicator plugins."""

    indicator_name: str = "base"

    @abstractmethod
    def compute(self, prices: list[Decimal], **parameters: Any) -> Decimal | None:
        """Compute indicator value from a price series."""
