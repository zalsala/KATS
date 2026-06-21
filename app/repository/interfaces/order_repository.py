"""Order repository interface."""

from __future__ import annotations

from typing import Protocol

from app.domain.order.order import Order


class OrderRepository(Protocol):
    """Persistence contract for orders."""

    def save(self, order: Order) -> None:
        """Persist an order."""

    def get(self, order_number: str) -> Order | None:
        """Load an order by order number."""

    def list_all(self) -> list[Order]:
        """Return all stored orders."""

    def update_status(self, order_number: str, status: str) -> bool:
        """Update an order status."""
