"""TR ID registry for KIS OpenAPI metadata."""

from __future__ import annotations

from app.broker.kis.api.metadata import ApiMetadata


class TrIdRegistry:
    """Registry mapping TR IDs to API metadata."""

    def __init__(self, entries: tuple[ApiMetadata, ...] | None = None) -> None:
        """Initialize the registry.

        Args:
            entries: Optional metadata entries. Uses default seed data when omitted.
        """
        from app.broker.kis.api.seeds import DEFAULT_API_METADATA

        source = entries if entries is not None else DEFAULT_API_METADATA
        self._by_tr_id: dict[str, ApiMetadata] = {}
        self._register_entries(source)

    def _register_entries(self, entries: tuple[ApiMetadata, ...]) -> None:
        for entry in entries:
            if entry.tr_id:
                self.register(entry.tr_id, entry)
            mock_tr_id = entry.mock_tr_id
            if mock_tr_id and mock_tr_id != entry.tr_id:
                self.register(mock_tr_id, entry)

    def register(self, tr_id: str, metadata: ApiMetadata) -> None:
        """Register a TR ID mapping.

        Args:
            tr_id: TR ID value.
            metadata: Associated API metadata.

        Raises:
            ValueError: When the TR ID is already registered to another API.
        """
        existing = self._by_tr_id.get(tr_id)
        if existing is not None and existing.api_key != metadata.api_key:
            msg = f"Duplicate tr_id registration: {tr_id}"
            raise ValueError(msg)
        self._by_tr_id[tr_id] = metadata

    def get(self, tr_id: str) -> ApiMetadata | None:
        """Return metadata for a TR ID.

        Args:
            tr_id: TR ID value.

        Returns:
            Matching metadata or None.
        """
        return self._by_tr_id.get(tr_id)

    def contains(self, tr_id: str) -> bool:
        """Return True when the TR ID is registered."""
        return tr_id in self._by_tr_id

    def all(self) -> tuple[ApiMetadata, ...]:
        """Return unique metadata entries registered by TR ID."""
        seen: set[str] = set()
        result: list[ApiMetadata] = []
        for metadata in self._by_tr_id.values():
            if metadata.api_key in seen:
                continue
            seen.add(metadata.api_key)
            result.append(metadata)
        return tuple(result)

    def validate(self) -> None:
        """Validate TR ID registry integrity.

        Raises:
            ValueError: When registry validation fails.
        """
        for tr_id, metadata in self._by_tr_id.items():
            metadata.validate()
            if metadata.tr_id and metadata.tr_id != tr_id and metadata.mock_tr_id != tr_id:
                msg = f"TR ID {tr_id} is not declared on metadata {metadata.api_key}"
                raise ValueError(msg)

        keys = [item.api_key for item in self.all()]
        if len(keys) != len(set(keys)):
            msg = "Duplicate API keys detected in TR ID registry"
            raise ValueError(msg)
