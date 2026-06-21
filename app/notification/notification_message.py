"""Notification message model."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.core.logging.masker import SensitiveDataMasker
from app.notification.notification_category import NotificationCategory


@dataclass(frozen=True, slots=True)
class NotificationMessage:
    """User-facing notification payload."""

    category: NotificationCategory
    title: str
    body: str
    level: str = "INFO"
    notification_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_event: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    context: dict[str, Any] = field(default_factory=dict)

    def masked(self, masker: SensitiveDataMasker | None = None) -> NotificationMessage:
        """Return a copy with sensitive values masked."""
        sensitive_masker = masker or SensitiveDataMasker()
        masked_context = {
            key: sensitive_masker.mask(str(value)) if isinstance(value, str) else value
            for key, value in self.context.items()
        }
        return NotificationMessage(
            notification_id=self.notification_id,
            category=self.category,
            title=sensitive_masker.mask(self.title),
            body=sensitive_masker.mask(self.body),
            level=self.level,
            source_event=self.source_event,
            created_at=self.created_at,
            context=masked_context,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the notification for providers and UI events."""
        return {
            "notification_id": self.notification_id,
            "category": str(self.category),
            "title": self.title,
            "body": self.body,
            "level": self.level,
            "source_event": self.source_event,
            "created_at": self.created_at.isoformat(),
            "context": self.context,
        }
