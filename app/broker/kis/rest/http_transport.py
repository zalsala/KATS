"""HTTP transport for KIS REST API calls."""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol

from app.broker.kis.exceptions.rest_exceptions import BrokerTimeoutError, NetworkError


@dataclass(frozen=True, slots=True)
class RestHttpResponse:
    """HTTP response wrapper for REST transport.

    Attributes:
        status_code: HTTP status code.
        body: Parsed JSON object when available.
        text: Raw response text.
        headers: Response headers.
    """

    status_code: int
    body: dict[str, Any]
    text: str
    headers: dict[str, str]


class RestHttpTransport(Protocol):
    """Protocol for KIS REST HTTP transport."""

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        body: dict[str, Any] | None = None,
        timeout_seconds: float,
    ) -> RestHttpResponse:
        """Execute an HTTP request.

        Args:
            method: HTTP method such as GET or POST.
            url: Fully qualified request URL.
            headers: Request headers.
            body: Optional JSON body for POST requests.
            timeout_seconds: Request timeout in seconds.

        Returns:
            Parsed HTTP response.
        """
        ...


class UrllibRestHttpTransport:
    """Default REST transport backed by ``urllib.request``."""

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        body: dict[str, Any] | None = None,
        timeout_seconds: float,
    ) -> RestHttpResponse:
        """Execute an HTTP request via urllib.

        Args:
            method: HTTP method such as GET or POST.
            url: Fully qualified request URL.
            headers: Request headers.
            body: Optional JSON body for POST requests.
            timeout_seconds: Request timeout in seconds.

        Returns:
            Parsed HTTP response.

        Raises:
            BrokerTimeoutError: When the request times out.
            NetworkError: When a network failure occurs.
        """
        payload = None
        if body is not None:
            payload = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(  # noqa: S310
            url=url,
            data=payload,
            headers=headers,
            method=method.upper(),
        )
        context = ssl.create_default_context()
        try:
            with urllib.request.urlopen(  # noqa: S310
                request,
                timeout=timeout_seconds,
                context=context,
            ) as response:
                text = response.read().decode("utf-8")
                response_headers = {key.lower(): value for key, value in response.headers.items()}
                return RestHttpResponse(
                    status_code=response.status,
                    body=_parse_json(text),
                    text=text,
                    headers=response_headers,
                )
        except urllib.error.HTTPError as exc:
            text = exc.read().decode("utf-8", errors="replace")
            response_headers = {key.lower(): value for key, value in exc.headers.items()}
            return RestHttpResponse(
                status_code=exc.code,
                body=_parse_json(text),
                text=text,
                headers=response_headers,
            )
        except TimeoutError as exc:
            msg = f"REST request timed out after {timeout_seconds}s"
            raise BrokerTimeoutError(msg) from exc
        except urllib.error.URLError as exc:
            msg = f"REST network error: {exc.reason}"
            raise NetworkError(msg) from exc


def build_url(base_url: str, path: str, query: dict[str, Any] | None = None) -> str:
    """Build a fully qualified REST URL.

    Args:
        base_url: KIS REST base URL.
        path: API path beginning with ``/``.
        query: Optional query parameters for GET requests.

    Returns:
        Fully qualified URL string.
    """
    normalized_base = base_url.rstrip("/")
    normalized_path = path if path.startswith("/") else f"/{path}"
    url = f"{normalized_base}{normalized_path}"
    if not query:
        return url
    encoded = urllib.parse.urlencode({key: str(value) for key, value in query.items()})
    return f"{url}?{encoded}"


def _parse_json(text: str) -> dict[str, Any]:
    if not text:
        return {}
    try:
        loaded = json.loads(text)
    except json.JSONDecodeError:
        return {}
    if isinstance(loaded, dict):
        return loaded
    return {}
