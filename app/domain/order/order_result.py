"""Order submission result."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.order.order import Order


@dataclass(slots=True)
class OrderResult:
    """Result returned after an order API call."""

    success: bool
    order_number: str
    order_branch: str
    order_time: str
    rt_cd: str
    msg_cd: str
    msg1: str
    order: Order | None = None
