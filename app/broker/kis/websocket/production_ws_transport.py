"""Production WebSocket transport for KIS realtime connections."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from app.core.constants import DEFAULT_WS_TIMEOUT

if TYPE_CHECKING:
    from websocket import WebSocket

logger = logging.getLogger(__name__)

ConnectionFactory = Callable[..., Any]


class ProductionWsTransport:
    """WebSocket transport backed by ``websocket-client``.

    Handles connect/send/receive/close only. Authentication headers and
    approval keys are supplied by ``KisWebSocketClient`` at connect time.
    """

    def __init__(
        self,
        *,
        default_timeout: float = DEFAULT_WS_TIMEOUT,
        connection_factory: ConnectionFactory | None = None,
    ) -> None:
        self._default_timeout = default_timeout
        self._connection_factory = connection_factory or _create_connection
        self._connection: WebSocket | None = None

    @property
    def is_open(self) -> bool:
        """Return True when the underlying socket connection is open."""
        if self._connection is None:
            return False
        return bool(getattr(self._connection, "connected", False))

    def connect(self, url: str, headers: dict[str, str]) -> None:
        """Open a WebSocket connection to the given URL."""
        self.close()
        header_list = [f"{key}: {value}" for key, value in headers.items()]
        try:
            self._connection = self._connection_factory(
                url,
                header=header_list,
                timeout=self._default_timeout,
            )
        except Exception as exc:
            self._connection = None
            msg = f"WebSocket connection failed: {exc}"
            logger.error(msg)
            raise ConnectionError(msg) from exc
        logger.debug("WebSocket transport connected url=%s", url)

    def send(self, message: str) -> None:
        """Send a text frame."""
        connection = self._require_connection()
        try:
            connection.send(message)
        except Exception as exc:
            msg = f"WebSocket send failed: {exc}"
            logger.error(msg)
            raise ConnectionError(msg) from exc

    def receive(self, timeout: float | None = None) -> str | None:
        """Receive the next text frame, or None on timeout."""
        connection = self._require_connection()
        effective_timeout = self._default_timeout if timeout is None else timeout
        connection.settimeout(effective_timeout)
        try:
            frame = connection.recv()
        except Exception as exc:
            if _is_timeout_error(exc):
                return None
            msg = f"WebSocket receive failed: {exc}"
            logger.error(msg)
            raise ConnectionError(msg) from exc
        if frame is None:
            return None
        if isinstance(frame, bytes):
            return frame.decode("utf-8")
        return str(frame)

    def close(self) -> None:
        """Close the WebSocket connection."""
        if self._connection is None:
            return
        try:
            self._connection.close()
        except Exception:
            logger.debug("WebSocket close ignored transport error", exc_info=True)
        finally:
            self._connection = None

    def _require_connection(self) -> WebSocket:
        if not self.is_open or self._connection is None:
            msg = "WebSocket is not connected"
            raise ConnectionError(msg)
        return self._connection


def build_production_ws_transport(
    *,
    default_timeout: float = DEFAULT_WS_TIMEOUT,
) -> ProductionWsTransport:
    """Create a production WebSocket transport."""
    return ProductionWsTransport(default_timeout=default_timeout)


def _create_connection(url: str, *, header: list[str], timeout: float) -> Any:
    import websocket

    return websocket.create_connection(url, header=header, timeout=timeout)


def _is_timeout_error(exc: Exception) -> bool:
    import websocket

    timeout_types: tuple[type[BaseException], ...] = (TimeoutError,)
    ws_timeout = getattr(websocket, "WebSocketTimeoutException", None)
    if ws_timeout is not None:
        timeout_types = (*timeout_types, ws_timeout)
    return isinstance(exc, timeout_types)
