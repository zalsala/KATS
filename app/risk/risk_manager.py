"""Risk runtime state manager."""

from __future__ import annotations

import threading
from datetime import UTC, date, datetime
from decimal import Decimal


class RiskManager:
    """Tracks emergency stop, pending orders, and daily loss baseline."""

    def __init__(self, *, emergency_stop: bool = False) -> None:
        self._lock = threading.RLock()
        self._emergency_stop = emergency_stop
        self._pending_symbols: set[str] = set()
        self._daily_start_asset: Decimal | None = None
        self._daily_start_date: date | None = None

    @property
    def emergency_stop(self) -> bool:
        """Return whether emergency stop is active."""
        with self._lock:
            return self._emergency_stop

    def set_emergency_stop(self, active: bool) -> None:
        """Enable or disable emergency stop."""
        with self._lock:
            self._emergency_stop = active

    def has_pending_order(self, symbol_code: str) -> bool:
        """Return whether a pending order exists for the symbol."""
        with self._lock:
            return symbol_code in self._pending_symbols

    def register_pending_order(self, symbol_code: str) -> None:
        """Mark a symbol as having a pending order."""
        with self._lock:
            self._pending_symbols.add(symbol_code)

    def clear_pending_order(self, symbol_code: str) -> None:
        """Clear pending order state for a symbol."""
        with self._lock:
            self._pending_symbols.discard(symbol_code)

    def clear_all_pending_orders(self) -> None:
        """Clear all pending order markers."""
        with self._lock:
            self._pending_symbols.clear()

    def ensure_daily_baseline(self, total_asset: Decimal) -> None:
        """Initialize daily asset baseline when the trading day changes."""
        today = datetime.now(UTC).date()
        with self._lock:
            if self._daily_start_date != today or self._daily_start_asset is None:
                self._daily_start_date = today
                self._daily_start_asset = total_asset

    def daily_loss_ratio(self, current_total_asset: Decimal) -> Decimal:
        """Return daily loss ratio relative to the day-start asset."""
        with self._lock:
            if self._daily_start_asset is None or self._daily_start_asset <= 0:
                return Decimal("0")
            loss = self._daily_start_asset - current_total_asset
            if loss <= 0:
                return Decimal("0")
            return loss / self._daily_start_asset
