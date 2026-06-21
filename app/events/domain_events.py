"""Concrete domain event types."""

from __future__ import annotations

from typing import Any

from app.events.base_event import BaseEvent
from app.events.event_types import EventType


class MarketDataEvent(BaseEvent):
    """Market data update event."""

    def __init__(
        self,
        *,
        source: str,
        payload: dict[str, Any] | None = None,
        event_name: str = "market_data.updated",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            event_type=EventType.MARKET_DATA,
            source=source,
            payload=payload or {},
            event_name=event_name,
            **kwargs,
        )


class OrderEvent(BaseEvent):
    """Order lifecycle event."""

    def __init__(
        self,
        *,
        source: str,
        payload: dict[str, Any] | None = None,
        event_name: str = "order.updated",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            event_type=EventType.ORDER,
            source=source,
            payload=payload or {},
            event_name=event_name,
            **kwargs,
        )


class ExecutionEvent(BaseEvent):
    """Order execution event."""

    def __init__(
        self,
        *,
        source: str,
        payload: dict[str, Any] | None = None,
        event_name: str = "execution.received",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            event_type=EventType.EXECUTION,
            source=source,
            payload=payload or {},
            event_name=event_name,
            **kwargs,
        )


class AccountEvent(BaseEvent):
    """Account update event."""

    def __init__(
        self,
        *,
        source: str,
        payload: dict[str, Any] | None = None,
        event_name: str = "account.updated",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            event_type=EventType.ACCOUNT,
            source=source,
            payload=payload or {},
            event_name=event_name,
            **kwargs,
        )


class PortfolioEvent(BaseEvent):
    """Portfolio update event."""

    def __init__(
        self,
        *,
        source: str,
        payload: dict[str, Any] | None = None,
        event_name: str = "portfolio.updated",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            event_type=EventType.PORTFOLIO,
            source=source,
            payload=payload or {},
            event_name=event_name,
            **kwargs,
        )


class StrategyEvent(BaseEvent):
    """Strategy signal or lifecycle event."""

    def __init__(
        self,
        *,
        source: str,
        payload: dict[str, Any] | None = None,
        event_name: str = "strategy.updated",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            event_type=EventType.STRATEGY,
            source=source,
            payload=payload or {},
            event_name=event_name,
            **kwargs,
        )


class RiskEvent(BaseEvent):
    """Risk check event."""

    def __init__(
        self,
        *,
        source: str,
        payload: dict[str, Any] | None = None,
        event_name: str = "risk.checked",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            event_type=EventType.RISK,
            source=source,
            payload=payload or {},
            event_name=event_name,
            **kwargs,
        )


class SystemEvent(BaseEvent):
    """System lifecycle event."""

    def __init__(
        self,
        *,
        source: str,
        payload: dict[str, Any] | None = None,
        event_name: str = "system.updated",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            event_type=EventType.SYSTEM,
            source=source,
            payload=payload or {},
            event_name=event_name,
            **kwargs,
        )


class ErrorEvent(BaseEvent):
    """Error notification event."""

    def __init__(
        self,
        *,
        source: str,
        payload: dict[str, Any] | None = None,
        event_name: str = "error.occurred",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            event_type=EventType.ERROR,
            source=source,
            payload=payload or {},
            event_name=event_name,
            **kwargs,
        )
