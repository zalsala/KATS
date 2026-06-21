"""Logging system constants for KATS."""

from __future__ import annotations

from enum import StrEnum
from typing import Final

LOG_ROOT_NAME: Final[str] = "kats"

CORRELATION_ID_FIELD: Final[str] = "correlation_id"
LATENCY_MS_FIELD: Final[str] = "latency_ms"
OPERATION_FIELD: Final[str] = "operation"

DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"
DAILY_ROTATION_WHEN: Final[str] = "midnight"
DAILY_ROTATION_INTERVAL: Final[int] = 1

TEXT_LOG_FORMAT: Final[str] = (
    "%(asctime)s | %(levelname)-8s | %(name)s | " "[%(correlation_id)s] | %(message)s"
)


class LogCategory(StrEnum):
    """Log file categories aligned with KATS operational domains."""

    SYSTEM = "system"
    API = "api"
    ORDER = "order"
    STRATEGY = "strategy"
    WEBSOCKET = "websocket"
    DATABASE = "database"
    ERROR = "error"


LOG_CATEGORIES: Final[tuple[LogCategory, ...]] = tuple(LogCategory)

CATEGORY_LOG_FILES: Final[dict[LogCategory, str]] = {
    LogCategory.SYSTEM: "system.log",
    LogCategory.API: "api.log",
    LogCategory.ORDER: "order.log",
    LogCategory.STRATEGY: "strategy.log",
    LogCategory.WEBSOCKET: "websocket.log",
    LogCategory.DATABASE: "database.log",
    LogCategory.ERROR: "error.log",
}

CATEGORY_LOGGER_NAMES: Final[dict[LogCategory, str]] = {
    category: f"{LOG_ROOT_NAME}.{category.value}" for category in LogCategory
}

DEFAULT_CATEGORY: Final[LogCategory] = LogCategory.SYSTEM

PERFORMANCE_LOG_THRESHOLD_MS: Final[float] = 0.0
