"""Notification category definitions."""

from __future__ import annotations

from enum import StrEnum


class NotificationCategory(StrEnum):
    """Supported notification categories."""

    ORDER_SUCCESS = "order_success"
    ORDER_FAILURE = "order_failure"
    EXECUTION = "execution"
    RISK_REJECTED = "risk_rejected"
    EMERGENCY_STOP = "emergency_stop"
    STRATEGY_STARTED = "strategy_started"
    STRATEGY_STOPPED = "strategy_stopped"
    WEBSOCKET_DISCONNECTED = "websocket_disconnected"
    SCHEDULER_FAILURE = "scheduler_failure"
    SYSTEM_ERROR = "system_error"
