"""UI notification provider."""

from __future__ import annotations

from app.events.domain_events import SystemEvent
from app.events.event_bus_service import EventBusService
from app.notification.notification_channel import NotificationChannel
from app.notification.notification_message import NotificationMessage


class UiNotificationProvider:
    """Publish UI notifications through EventBus instead of touching widgets."""

    def __init__(self, *, event_bus: EventBusService | None = None) -> None:
        self._event_bus = event_bus

    def bind_event_bus(self, event_bus: EventBusService) -> None:
        """Attach EventBus after service construction."""
        self._event_bus = event_bus

    @property
    def channel(self) -> NotificationChannel:
        return NotificationChannel.UI

    def send(self, message: NotificationMessage) -> bool:
        if self._event_bus is None:
            return False
        self._event_bus.publish(
            SystemEvent(
                source="notification",
                event_name="notification.created",
                payload=message.to_dict(),
            )
        )
        return True
