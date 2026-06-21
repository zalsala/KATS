"""EventBus to notification mapping."""

from __future__ import annotations

from app.events.base_event import BaseEvent
from app.events.event_bus_service import EventBusService
from app.events.event_types import EventType
from app.notification.notification_category import NotificationCategory
from app.notification.notification_manager import NotificationManager
from app.notification.notification_message import NotificationMessage


class NotificationEventHandler:
    """Subscribe to domain events and create user notifications."""

    def __init__(self, *, manager: NotificationManager) -> None:
        self._manager = manager
        self._subscription_ids: list[str] = []

    @property
    def subscription_ids(self) -> tuple[str, ...]:
        return tuple(self._subscription_ids)

    def register(self, event_bus: EventBusService) -> tuple[str, ...]:
        """Subscribe notification handlers to EventBus."""
        self._subscription_ids = [
            event_bus.subscribe(EventType.ORDER, self.handle_order),
            event_bus.subscribe(EventType.EXECUTION, self.handle_execution),
            event_bus.subscribe(EventType.RISK, self.handle_risk),
            event_bus.subscribe(EventType.STRATEGY, self.handle_strategy),
            event_bus.subscribe(EventType.SYSTEM, self.handle_system),
            event_bus.subscribe(EventType.ERROR, self.handle_error),
        ]
        return tuple(self._subscription_ids)

    def unregister(self, event_bus: EventBusService) -> None:
        """Unsubscribe notification handlers."""
        for subscription_id in self._subscription_ids:
            event_bus.unsubscribe(subscription_id)
        self._subscription_ids.clear()

    def handle_order(self, event: BaseEvent) -> None:
        message = _map_order_event(event)
        if message is not None:
            self._manager.notify(message)

    def handle_execution(self, event: BaseEvent) -> None:
        payload = event.payload
        symbol = str(payload.get("symbol_code", payload.get("symbol", "")))
        quantity = str(payload.get("quantity", ""))
        price = str(payload.get("price", ""))
        self._manager.notify(
            NotificationMessage(
                category=NotificationCategory.EXECUTION,
                title="체결 발생",
                body=f"{symbol} {quantity}@{price} 체결",
                level="INFO",
                source_event=event.event_name,
                context={"symbol_code": symbol, "quantity": quantity, "price": price},
            )
        )

    def handle_risk(self, event: BaseEvent) -> None:
        payload = event.payload
        status = str(payload.get("status", "")).upper()
        violations = payload.get("violations", [])
        if _has_emergency_violation(violations):
            self._manager.notify(
                NotificationMessage(
                    category=NotificationCategory.EMERGENCY_STOP,
                    title="Emergency Stop",
                    body=str(payload.get("message", "Emergency stop is active")),
                    level="ERROR",
                    source_event=event.event_name,
                    context={"status": status},
                )
            )
            return
        if status == "REJECTED" or payload.get("approved") is False:
            self._manager.notify(
                NotificationMessage(
                    category=NotificationCategory.RISK_REJECTED,
                    title="Risk 거부",
                    body=str(payload.get("message", "Risk validation rejected the signal")),
                    level="WARN",
                    source_event=event.event_name,
                    context={"symbol_code": str(payload.get("symbol_code", ""))},
                )
            )

    def handle_strategy(self, event: BaseEvent) -> None:
        message = _map_strategy_event(event)
        if message is not None:
            self._manager.notify(message)

    def handle_system(self, event: BaseEvent) -> None:
        message = _map_system_event(event)
        if message is not None:
            self._manager.notify(message)

    def handle_error(self, event: BaseEvent) -> None:
        payload = event.payload
        self._manager.notify(
            NotificationMessage(
                category=NotificationCategory.SYSTEM_ERROR,
                title="시스템 오류",
                body=str(payload.get("message", event.event_name)),
                level="ERROR",
                source_event=event.event_name,
                context={"error_code": str(payload.get("error_code", ""))},
            )
        )


def _map_order_event(event: BaseEvent) -> NotificationMessage | None:
    payload = event.payload
    event_name = event.event_name.lower()
    status = str(payload.get("status", "")).lower()
    if "fail" in event_name or status in {"failed", "failure", "rejected", "error"}:
        return NotificationMessage(
            category=NotificationCategory.ORDER_FAILURE,
            title="주문 실패",
            body=str(payload.get("message", "Order request failed")),
            level="ERROR",
            source_event=event.event_name,
            context={"symbol_code": str(payload.get("symbol_code", ""))},
        )
    if "success" in event_name or status in {"success", "accepted", "submitted", "completed"}:
        return NotificationMessage(
            category=NotificationCategory.ORDER_SUCCESS,
            title="주문 성공",
            body=str(payload.get("message", "Order request accepted")),
            level="INFO",
            source_event=event.event_name,
            context={"symbol_code": str(payload.get("symbol_code", ""))},
        )
    return None


def _map_strategy_event(event: BaseEvent) -> NotificationMessage | None:
    payload = event.payload
    event_name = event.event_name.lower()
    state = str(payload.get("state", "")).lower()
    strategy_name = str(payload.get("strategy_name", payload.get("name", "")))

    if "start" in event_name or state == "running":
        return NotificationMessage(
            category=NotificationCategory.STRATEGY_STARTED,
            title="전략 시작",
            body=f"{strategy_name or 'Strategy'} started",
            level="INFO",
            source_event=event.event_name,
            context={"strategy_id": str(payload.get("strategy_id", ""))},
        )
    if "stop" in event_name or state == "stopped":
        return NotificationMessage(
            category=NotificationCategory.STRATEGY_STOPPED,
            title="전략 중지",
            body=f"{strategy_name or 'Strategy'} stopped",
            level="INFO",
            source_event=event.event_name,
            context={"strategy_id": str(payload.get("strategy_id", ""))},
        )
    return None


def _map_system_event(event: BaseEvent) -> NotificationMessage | None:
    event_name = event.event_name.lower()
    payload = event.payload

    if event_name == "notification.created":
        return None

    if "websocket" in event_name and ("disconnect" in event_name or "closed" in event_name):
        return NotificationMessage(
            category=NotificationCategory.WEBSOCKET_DISCONNECTED,
            title="WebSocket 연결 끊김",
            body=str(payload.get("message", "WebSocket connection lost")),
            level="WARN",
            source_event=event.event_name,
            context={"connection_id": str(payload.get("connection_id", ""))},
        )

    if event_name == "scheduler.task.failed":
        return NotificationMessage(
            category=NotificationCategory.SCHEDULER_FAILURE,
            title="Scheduler 작업 실패",
            body=str(payload.get("message", "Scheduled task failed")),
            level="ERROR",
            source_event=event.event_name,
            context={"task_id": str(payload.get("task_id", ""))},
        )

    if payload.get("emergency_stop") is True:
        return NotificationMessage(
            category=NotificationCategory.EMERGENCY_STOP,
            title="Emergency Stop",
            body=str(payload.get("message", "Emergency stop activated")),
            level="ERROR",
            source_event=event.event_name,
        )

    return None


def _has_emergency_violation(violations: object) -> bool:
    if not isinstance(violations, list):
        return False
    for item in violations:
        if isinstance(item, dict) and item.get("rule_code") == "emergency_stop":
            return True
    return False
