"""Notification service exports."""

from app.service.notification.notification_service import (
    NotificationService,
    build_notification_service,
)

__all__ = ["NotificationService", "build_notification_service"]
