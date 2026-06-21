"""Minimal order entity for in-memory state tracking."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Order:
    """Simple order state stored by OrderService."""

    order_number: str
    order_branch: str
    symbol_code: str
    side: str
    quantity: str
    price: str
    status: str = "submitted"
