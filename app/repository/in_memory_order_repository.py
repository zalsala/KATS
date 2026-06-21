"""In-memory order repository for tests."""

from __future__ import annotations

import threading

from app.domain.order.order import Order


class InMemoryOrderRepository:
    """Thread-safe in-memory order storage."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._orders: dict[str, Order] = {}

    def save(self, order: Order) -> None:
        with self._lock:
            self._orders[order.order_number] = order

    def get(self, order_number: str) -> Order | None:
        with self._lock:
            return self._orders.get(order_number)

    def list_all(self) -> list[Order]:
        with self._lock:
            return list(self._orders.values())

    def update_status(self, order_number: str, status: str) -> bool:
        with self._lock:
            order = self._orders.get(order_number)
            if order is None:
                return False
            order.status = status
            return True
