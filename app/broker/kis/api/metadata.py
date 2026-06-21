"""KIS API metadata model."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.broker.kis.api.enums import ApiCategory, HttpMethod

API_KEY_PATTERN = re.compile(r"^[a-z0-9_]+(?:\.[a-z0-9_]+)+$")
UAPI_PATH_PATTERN = re.compile(r"^/uapi/[a-z0-9-]+/v1/[a-z0-9-]+/[a-z0-9-]+$")
AUTH_PATH_PATTERN = re.compile(r"^/(?:oauth2/[A-Za-z0-9]+|uapi/hashkey)$")
TR_ID_PATTERN = re.compile(r"^[A-Z0-9]{8,13}$")
MOCK_TR_ID_PREFIXES = frozenset({"T", "J", "C"})


def resolve_mock_tr_id(tr_id: str) -> str:
    """Resolve the mock (VTS) TR ID from a real TR ID.

    Official ``kis_auth.py`` replaces the first character with ``V`` when the
    real TR ID starts with ``T``, ``J``, or ``C``.

    Args:
        tr_id: Real-environment TR ID.

    Returns:
        Mock TR ID or the original value when conversion does not apply.
    """
    if tr_id and tr_id[0] in MOCK_TR_ID_PREFIXES:
        return f"V{tr_id[1:]}"
    return tr_id


@dataclass(frozen=True, slots=True)
class ApiMetadata:
    """Metadata describing a single KIS REST API endpoint.

    Attributes:
        api_key: Unique registry key (e.g. ``domestic_stock.inquire_price``).
        name: Human-readable API name.
        category: Official API category.
        method: HTTP method.
        path: REST path relative to the KIS base URL.
        tr_id: Real-environment TR ID. Empty for auth endpoints without TR IDs.
        description: Short API description.
        sub_category: KIS path segment such as ``quotations`` or ``trading``.
        requires_hashkey: True when HashKey is required before calling the API.
        supports_pagination: True when ``tr_cont`` pagination is supported.
        enabled: False when the API is registered but excluded from KATS scope.
    """

    api_key: str
    name: str
    category: ApiCategory
    method: HttpMethod
    path: str
    tr_id: str
    description: str
    sub_category: str = ""
    requires_hashkey: bool = False
    supports_pagination: bool = False
    enabled: bool = True

    @property
    def mock_tr_id(self) -> str:
        """Return the mock TR ID derived from the real TR ID."""
        if not self.tr_id:
            return ""
        return resolve_mock_tr_id(self.tr_id)

    @property
    def endpoint_key(self) -> str:
        """Return a stable endpoint lookup key."""
        return f"{self.method.value}:{self.path}"

    def validate(self) -> None:
        """Validate metadata fields.

        Raises:
            ValueError: When metadata is invalid.
        """
        if not API_KEY_PATTERN.match(self.api_key):
            msg = f"Invalid api_key format: {self.api_key}"
            raise ValueError(msg)
        if self.category == ApiCategory.AUTH:
            if not AUTH_PATH_PATTERN.match(self.path):
                msg = f"Invalid auth path format: {self.path}"
                raise ValueError(msg)
        elif not UAPI_PATH_PATTERN.match(self.path):
            msg = f"Invalid UAPI path format: {self.path}"
            raise ValueError(msg)
        if self.tr_id and not TR_ID_PATTERN.match(self.tr_id):
            msg = f"Invalid tr_id format: {self.tr_id}"
            raise ValueError(msg)
        if self.mock_tr_id and not TR_ID_PATTERN.match(self.mock_tr_id):
            msg = f"Invalid mock tr_id format: {self.mock_tr_id}"
            raise ValueError(msg)
