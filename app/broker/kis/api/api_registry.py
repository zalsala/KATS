"""Combined KIS API registry."""

from __future__ import annotations

from dataclasses import dataclass

from app.broker.kis.api.endpoint_registry import EndpointRegistry
from app.broker.kis.api.metadata import ApiMetadata
from app.broker.kis.api.tr_id_registry import TrIdRegistry


@dataclass(frozen=True, slots=True)
class ApiRegistry:
    """Combined TR ID and endpoint registry for KIS APIs."""

    tr_ids: TrIdRegistry
    endpoints: EndpointRegistry

    @classmethod
    def default(cls) -> ApiRegistry:
        """Create a registry loaded with default official seed metadata."""
        return cls(tr_ids=TrIdRegistry(), endpoints=EndpointRegistry())

    @classmethod
    def from_entries(cls, entries: tuple[ApiMetadata, ...]) -> ApiRegistry:
        """Create a registry from custom metadata entries.

        Args:
            entries: API metadata entries to register.

        Returns:
            Configured combined registry.
        """
        return cls(tr_ids=TrIdRegistry(entries), endpoints=EndpointRegistry(entries))

    def validate(self) -> None:
        """Validate TR ID and endpoint registries together.

        Raises:
            ValueError: When cross-registry validation fails.
        """
        self.tr_ids.validate()
        self.endpoints.validate()
        self._validate_cross_registry()

    def _validate_cross_registry(self) -> None:
        for metadata in self.endpoints.all():
            if not metadata.tr_id:
                continue
            tr_lookup = self.tr_ids.get(metadata.tr_id)
            if tr_lookup is None:
                msg = f"Endpoint {metadata.api_key} tr_id is missing from TR ID registry"
                raise ValueError(msg)
            if tr_lookup.api_key != metadata.api_key:
                msg = f"TR ID registry mismatch for {metadata.api_key}"
                raise ValueError(msg)

            endpoint_lookup = self.endpoints.get(metadata.method, metadata.path)
            if endpoint_lookup is None:
                msg = f"Endpoint lookup failed for {metadata.api_key}"
                raise ValueError(msg)

            mock_tr_id = metadata.mock_tr_id
            if mock_tr_id and mock_tr_id != metadata.tr_id:
                mock_lookup = self.tr_ids.get(mock_tr_id)
                if mock_lookup is None or mock_lookup.api_key != metadata.api_key:
                    msg = f"Mock TR ID registry mismatch for {metadata.api_key}"
                    raise ValueError(msg)
