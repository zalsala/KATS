"""Event type enumeration."""

from __future__ import annotations

from enum import StrEnum


class EventType(StrEnum):
    """Supported event categories for KATS EventBus."""

    MARKET_DATA = "market_data"
    ORDER = "order"
    EXECUTION = "execution"
    ACCOUNT = "account"
    PORTFOLIO = "portfolio"
    STRATEGY = "strategy"
    RISK = "risk"
    SYSTEM = "system"
    ERROR = "error"
