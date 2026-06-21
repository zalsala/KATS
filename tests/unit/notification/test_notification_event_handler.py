"""NotificationEventHandler tests."""

from __future__ import annotations

import pytest
from tests.fixtures.notification_fixtures import build_test_notification_service

from app.events.domain_events import ExecutionEvent, OrderEvent, RiskEvent, SystemEvent
from app.notification.notification_category import NotificationCategory

pytestmark = pytest.mark.unit


def test_order_success_event_creates_notification() -> None:
    service = build_test_notification_service(enable_ui=False, enable_plugins=False)
    assert service.event_bus is not None
    service.start(service.event_bus)
    service.event_bus.publish(
        OrderEvent(
            source="order_service",
            event_name="order.success",
            payload={"status": "success", "symbol_code": "005930", "message": "accepted"},
        )
    )
    stored = service.list_notifications()
    assert stored[-1]["category"] == NotificationCategory.ORDER_SUCCESS


def test_risk_rejected_event_creates_notification() -> None:
    service = build_test_notification_service(enable_ui=False, enable_plugins=False)
    assert service.event_bus is not None
    service.start(service.event_bus)
    service.event_bus.publish(
        RiskEvent(
            source="risk_engine",
            event_name="risk.validated",
            payload={
                "status": "REJECTED",
                "approved": False,
                "message": "max order amount exceeded",
                "symbol_code": "005930",
            },
        )
    )
    stored = service.list_notifications()
    assert stored[-1]["category"] == NotificationCategory.RISK_REJECTED


def test_scheduler_failure_system_event_creates_notification() -> None:
    service = build_test_notification_service(enable_ui=False, enable_plugins=False)
    assert service.event_bus is not None
    service.start(service.event_bus)
    service.event_bus.publish(
        SystemEvent(
            source="scheduler",
            event_name="scheduler.task.failed",
            payload={"task_id": "task-1", "message": "StrategyService is not configured"},
        )
    )
    stored = service.list_notifications()
    assert stored[-1]["category"] == NotificationCategory.SCHEDULER_FAILURE


def test_execution_event_creates_notification() -> None:
    service = build_test_notification_service(enable_ui=False, enable_plugins=False)
    assert service.event_bus is not None
    service.start(service.event_bus)
    service.event_bus.publish(
        ExecutionEvent(
            source="broker",
            payload={"symbol_code": "005930", "quantity": "1", "price": "70000"},
        )
    )
    stored = service.list_notifications()
    assert stored[-1]["category"] == NotificationCategory.EXECUTION
