"""HTTP transport abstraction for KIS authentication APIs."""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class HttpResponse:
    """Minimal HTTP response wrapper for auth clients.

    Attributes:
        status_code: HTTP status code.
        body: Parsed JSON body when available, otherwise empty dict.
        text: Raw response text.
    """

    status_code: int
    body: dict[str, Any]
    text: str


class HttpTransport(Protocol):
    """Protocol for JSON POST requests used by authentication clients."""

    def post_json(
        self,
        url: str,
        headers: dict[str, str],
        body: dict[str, Any],
    ) -> HttpResponse:
        """Send a JSON POST request.

        Args:
            url: Fully qualified request URL.
            headers: HTTP headers.
            body: JSON-serializable request body.

        Returns:
            Parsed HTTP response.
        """
        ...


class UrllibHttpTransport:
    """Default HTTP transport backed by ``urllib.request``."""

    def __init__(self, *, timeout_seconds: float = 10.0) -> None:
        """Initialize transport with a request timeout.

        Args:
            timeout_seconds: Socket timeout in seconds.
        """
        self._timeout_seconds = timeout_seconds

    def post_json(
        self,
        url: str,
        headers: dict[str, str],
        body: dict[str, Any],
    ) -> HttpResponse:
        """Send a JSON POST request via urllib.

        Args:
            url: Fully qualified request URL.
            headers: HTTP headers.
            body: JSON-serializable request body.

        Returns:
            Parsed HTTP response.
        """
        payload = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(  # noqa: S310
            url=url,
            data=payload,
            headers=headers,
            method="POST",
        )
        context = ssl.create_default_context()
        try:
            with urllib.request.urlopen(  # noqa: S310
                request,
                timeout=self._timeout_seconds,
                context=context,
            ) as response:
                text = response.read().decode("utf-8")
                status_code = response.status
        except urllib.error.HTTPError as exc:
            text = exc.read().decode("utf-8", errors="replace")
            status_code = exc.code
        parsed_body = _parse_json(text)
        return HttpResponse(status_code=status_code, body=parsed_body, text=text)


def _parse_json(text: str) -> dict[str, Any]:
    """Parse JSON text into a dictionary.

    Args:
        text: Raw response text.

    Returns:
        Parsed dictionary or empty dict when parsing fails.
    """
    if not text:
        return {}
    try:
        loaded = json.loads(text)
    except json.JSONDecodeError:
        return {}
    if isinstance(loaded, dict):
        return loaded
    return {}
