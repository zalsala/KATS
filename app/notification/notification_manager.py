"""Notification dispatch manager."""

from __future__ import annotations

import logging
from typing import Any

from app.core.logging.masker import SensitiveDataMasker
from app.notification.in_memory_notification_store import InMemoryNotificationStore
from app.notification.notification_message import NotificationMessage
from app.notification.providers.base import NotificationProvider


def _resolve_logger() -> logging.Logger:
    return logging.getLogger(__name__)


class NotificationManager:
    """Mask, store, and dispatch notifications through configured providers."""

    def __init__(
        self,
        *,
        store: InMemoryNotificationStore | None = None,
        providers: list[NotificationProvider] | None = None,
        masker: SensitiveDataMasker | None = None,
    ) -> None:
        self._store = store or InMemoryNotificationStore()
        self._providers = providers or []
        self._masker = masker or SensitiveDataMasker()
        self._logger = _resolve_logger()

    @property
    def store(self) -> InMemoryNotificationStore:
        return self._store

    def register_provider(self, provider: NotificationProvider) -> None:
        """Add a notification provider."""
        self._providers.append(provider)

    @property
    def providers(self) -> tuple[NotificationProvider, ...]:
        """Return configured providers."""
        return tuple(self._providers)

    def has_provider(self, provider_type: type[object]) -> bool:
        """Return whether a provider type is already registered."""
        return any(isinstance(provider, provider_type) for provider in self._providers)

    def notify(self, message: NotificationMessage) -> dict[str, Any]:
        """Deliver a notification through all providers with failure isolation."""
        masked = message.masked(self._masker)
        self._store.save(masked)
        results: dict[str, Any] = {"notification_id": masked.notification_id, "channels": {}}
        for provider in self._providers:
            channel_name = str(provider.channel)
            try:
                results["channels"][channel_name] = provider.send(masked)
            except Exception:  # noqa: BLE001 - provider failures must not stop app
                self._logger.exception(
                    "Notification provider failed channel=%s notification_id=%s",
                    channel_name,
                    masked.notification_id,
                )
                results["channels"][channel_name] = False
        return results
