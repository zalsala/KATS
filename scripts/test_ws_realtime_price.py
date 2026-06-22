"""KIS VTS WebSocket realtime price subscription test for simulation."""

from __future__ import annotations

import logging
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

SAMSUNG_SYMBOL = "005930"
MAX_WAIT_SECONDS = 30.0
RECEIVE_POLL_TIMEOUT = 2.0


def _bootstrap_import_path() -> None:
    """Allow ``python scripts/test_ws_realtime_price.py`` from the project root."""
    root = Path(__file__).resolve().parents[1]
    scripts_dir = Path(__file__).resolve().parent
    for path_str in (str(root), str(scripts_dir)):
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


_bootstrap_import_path()

import vts_common  # noqa: E402

from app.bootstrap.broker_wiring import build_websocket_service_from_settings  # noqa: E402
from app.broker.kis.auth.http_transport import HttpTransport  # noqa: E402
from app.broker.kis.websocket.production_ws_transport import (  # noqa: E402
    ProductionWsTransport,
    build_production_ws_transport,
)
from app.broker.kis.websocket.subscription_manager import SubscriptionManager  # noqa: E402
from app.broker.kis.websocket.ws_transport import WsTransport  # noqa: E402
from app.config.app_settings import AppSettings  # noqa: E402
from app.core.constants import KIS_ACCOUNT_MOCK, KIS_VTS_WS_URL  # noqa: E402
from app.domain.realtime.entities import (  # noqa: E402
    ExecutionNotice,
    RealtimeOrderbook,
    RealtimePrice,
)
from app.dto.websocket.subscribe_request import SubscribeRequest  # noqa: E402
from app.service.websocket.websocket_service import WebSocketService  # noqa: E402

if TYPE_CHECKING:
    from app.broker.kis.auth import AuthenticationComponents

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class WsRealtimePriceTestResult:
    """Normalized WebSocket realtime price test response for CLI output."""

    rt_cd: str
    status: str
    msg1: str = ""
    subscribed: str = ""
    message_received: bool = False
    sample_message: str = ""


project_root = vts_common.project_root
load_simulation_settings = vts_common.load_simulation_settings


def validate_ws_prerequisites(settings: AppSettings) -> str | None:
    """Return an error message when VTS WebSocket prerequisites are not met."""
    error = vts_common.validate_simulation_environment(settings)
    if error is not None:
        return error
    if settings.secrets.account_type != KIS_ACCOUNT_MOCK:
        return "VTS mock account only (KIS_ACCOUNT_TYPE=mock)"
    if KIS_VTS_WS_URL not in settings.kis_websocket_url:
        return "WebSocket URL is not the KIS VTS simulation endpoint"
    return None


def build_price_subscribe_payload(approval_key: str, symbol_code: str) -> str:
    """Build the KIS WebSocket subscribe payload for realtime price."""
    manager = SubscriptionManager()
    request = SubscribeRequest.for_price(symbol_code)
    return manager.build_payload(approval_key, request)


def format_sample_message(
    entity: RealtimePrice | RealtimeOrderbook | ExecutionNotice,
) -> str:
    """Format a received entity for safe CLI output."""
    if isinstance(entity, RealtimePrice):
        return (
            f"symbol={entity.symbol_code} "
            f"price={entity.price} "
            f"trade_time={entity.trade_time}"
        )
    if isinstance(entity, RealtimeOrderbook):
        return (
            f"symbol={entity.symbol_code} "
            f"bid={entity.bid_price} ask={entity.ask_price}"
        )
    return (
        f"symbol={entity.symbol_code} "
        f"side={entity.side} "
        f"quantity={entity.executed_quantity}"
    )


def wait_for_realtime_message(
    service: WebSocketService,
    *,
    max_wait_seconds: float = MAX_WAIT_SECONDS,
    receive_timeout: float = RECEIVE_POLL_TIMEOUT,
) -> RealtimePrice | RealtimeOrderbook | ExecutionNotice | None:
    """Poll for the next realtime message within the allowed window."""
    deadline = time.monotonic() + max_wait_seconds
    while time.monotonic() < deadline:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        timeout = min(receive_timeout, remaining)
        entity = service.receive(timeout=timeout)
        if entity is not None:
            return entity
    return None


def run_ws_realtime_price_test(
    *,
    settings: AppSettings,
    symbol_code: str = SAMSUNG_SYMBOL,
    websocket_service: WebSocketService | None = None,
    auth: AuthenticationComponents | None = None,
    auth_transport: HttpTransport | None = None,
    ws_transport: WsTransport | ProductionWsTransport | None = None,
    max_wait_seconds: float = MAX_WAIT_SECONDS,
) -> WsRealtimePriceTestResult:
    """Connect to VTS WebSocket, subscribe to price, and wait for one message."""
    prerequisite_error = validate_ws_prerequisites(settings)
    if prerequisite_error is not None:
        return WsRealtimePriceTestResult(
            rt_cd="1",
            status="FAILED",
            msg1=prerequisite_error,
        )

    service = websocket_service
    try:
        auth_components = auth or vts_common.build_auth_components(
            settings,
            transport=auth_transport,
        )
        auth_components.approval_key_manager.issue()

        if service is None:
            transport = ws_transport or build_production_ws_transport()
            service = build_websocket_service_from_settings(
                settings=settings,
                auth=auth_components,
                ws_transport=transport,
            )

        service.connect()
        service.subscribe_price(symbol_code)

        entity = wait_for_realtime_message(service, max_wait_seconds=max_wait_seconds)
        if entity is None:
            return WsRealtimePriceTestResult(
                rt_cd="1",
                status="FAILED",
                msg1=f"No realtime message received within {int(max_wait_seconds)} seconds",
                subscribed=symbol_code,
                message_received=False,
            )

        return WsRealtimePriceTestResult(
            rt_cd="0",
            status="CONNECTED",
            subscribed=symbol_code,
            message_received=True,
            sample_message=format_sample_message(entity),
        )
    except Exception as exc:  # noqa: BLE001 - surface masked error to CLI
        return WsRealtimePriceTestResult(
            rt_cd="1",
            status="FAILED",
            msg1=vts_common.mask_text(str(exc)),
            subscribed=symbol_code,
        )
    finally:
        if service is not None and service.is_connected:
            service.disconnect()


def print_result(result: WsRealtimePriceTestResult) -> None:
    """Print WebSocket test summary without secrets."""
    print(f"rt_cd: {result.rt_cd}")
    if result.rt_cd == "0":
        print(f"status: {result.status}")
        print(f"subscribed: {result.subscribed}")
        print(f"message_received: {str(result.message_received).lower()}")
        print(f"sample_message: {result.sample_message}")
        return

    print(f"status: {result.status}")
    print(f"msg1: {result.msg1}")


def main() -> int:
    """Run the VTS WebSocket realtime price subscription test."""
    logging.basicConfig(level=logging.WARNING)
    root = project_root()
    settings = load_simulation_settings(root)
    result = run_ws_realtime_price_test(settings=settings, symbol_code=SAMSUNG_SYMBOL)
    print_result(result)
    return 0 if result.rt_cd == "0" else 1


if __name__ == "__main__":
    sys.exit(main())
