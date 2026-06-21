"""Endpoint registry for KIS OpenAPI metadata."""

from __future__ import annotations

from app.broker.kis.api.enums import HttpMethod
from app.broker.kis.api.metadata import ApiMetadata


class EndpointRegistry:
    """Registry mapping HTTP method and path pairs to API metadata."""

    def __init__(self, entries: tuple[ApiMetadata, ...] | None = None) -> None:
        """Initialize the registry.

        Args:
            entries: Optional metadata entries. Uses default seed data when omitted.
        """
        from app.broker.kis.api.seeds import DEFAULT_API_METADATA

        source = entries if entries is not None else DEFAULT_API_METADATA
        self._by_endpoint: dict[str, ApiMetadata] = {}
        for entry in source:
            self.register(entry)

    def register(self, metadata: ApiMetadata) -> None:
        """Register endpoint metadata.

        Args:
            metadata: API metadata to register.

        Raises:
            ValueError: When the endpoint is already registered to another API.
        """
        key = metadata.endpoint_key
        existing = self._by_endpoint.get(key)
        if existing is not None and existing.api_key != metadata.api_key:
            msg = f"Duplicate endpoint registration: {key}"
            raise ValueError(msg)
        self._by_endpoint[key] = metadata

    def get(self, method: HttpMethod | str, path: str) -> ApiMetadata | None:
        """Return metadata for an HTTP method and path pair.

        Args:
            method: HTTP method.
            path: REST path.

        Returns:
            Matching metadata or None.
        """
        method_value = method.value if isinstance(method, HttpMethod) else method.upper()
        return self._by_endpoint.get(f"{method_value}:{path}")

    def get_by_key(self, api_key: str) -> ApiMetadata | None:
        """Return metadata by API key.

        Args:
            api_key: Unique API registry key.

        Returns:
            Matching metadata or None.
        """
        for metadata in self._by_endpoint.values():
            if metadata.api_key == api_key:
                return metadata
        return None

    def all(self) -> tuple[ApiMetadata, ...]:
        """Return all registered metadata entries."""
        return tuple(self._by_endpoint.values())

    def by_category(self, category: str) -> tuple[ApiMetadata, ...]:
        """Return metadata entries filtered by category."""
        return tuple(item for item in self._by_endpoint.values() if item.category == category)

    def enabled(self) -> tuple[ApiMetadata, ...]:
        """Return metadata entries enabled for KATS."""
        return tuple(item for item in self._by_endpoint.values() if item.enabled)

    def validate(self) -> None:
        """Validate endpoint registry integrity.

        Raises:
            ValueError: When registry validation fails.
        """
        keys = [item.api_key for item in self._by_endpoint.values()]
        if len(keys) != len(set(keys)):
            msg = "Duplicate API keys detected in endpoint registry"
            raise ValueError(msg)

        endpoint_keys = list(self._by_endpoint.keys())
        if len(endpoint_keys) != len(set(endpoint_keys)):
            msg = "Duplicate endpoint keys detected"
            raise ValueError(msg)

        for metadata in self._by_endpoint.values():
            metadata.validate()
            if metadata.endpoint_key not in self._by_endpoint:
                msg = f"Missing endpoint key for {metadata.api_key}"
                raise ValueError(msg)
