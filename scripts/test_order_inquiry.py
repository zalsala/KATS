"""KIS daily order/execution inquiry test for simulation (VTS) environment."""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


def _bootstrap_import_path() -> None:
    """Allow ``python scripts/test_order_inquiry.py`` from the project root."""
    root = Path(__file__).resolve().parents[1]
    scripts_dir = Path(__file__).resolve().parent
    for path_str in (str(root), str(scripts_dir)):
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


_bootstrap_import_path()

import vts_common  # noqa: E402

from app.broker.kis.api import ApiRegistry  # noqa: E402
from app.broker.kis.api.account_api_keys import INQUIRE_DAILY_CCLD  # noqa: E402
from app.broker.kis.auth.auth_models import KIS_TIMEZONE  # noqa: E402
from app.broker.kis.rest.http_transport import RestHttpTransport  # noqa: E402
from app.broker.kis.rest.kis_rest_client import KisRestClient  # noqa: E402
from app.config.app_settings import AppSettings  # noqa: E402
from app.dto.account.trade_history_dto import TradeHistoryDto, TradeHistoryRequestDto  # noqa: E402
from app.repository.kis.account_api_resolver import build_account_api_resolver  # noqa: E402

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class OrderInquiryRow:
    """Single order/execution row for CLI output."""

    order_number: str
    symbol: str
    quantity: str
    status: str


@dataclass(frozen=True, slots=True)
class OrderInquiryTestResult:
    """Normalized daily order inquiry response for CLI output."""

    rt_cd: str
    msg_cd: str
    msg1: str
    order_count: int
    orders: tuple[OrderInquiryRow, ...] = ()


project_root = vts_common.project_root
load_simulation_settings = vts_common.load_simulation_settings
build_account_context = vts_common.build_account_context
build_account_rest_client = vts_common.build_rest_client


def default_inquiry_date_range() -> tuple[str, str]:
    """Return today's date range in KIS ``YYYYMMDD`` format."""
    today = datetime.now(KIS_TIMEZONE).strftime("%Y%m%d")
    return today, today


def resolve_order_status(row: TradeHistoryDto) -> str:
    """Map a trade history row to a simple execution status label."""
    quantity = row.executed_quantity.strip()
    if quantity and quantity != "0":
        return "filled"
    return "pending"


def to_order_rows(rows: list[TradeHistoryDto]) -> tuple[OrderInquiryRow, ...]:
    """Convert trade history DTO rows to CLI output rows."""
    return tuple(
        OrderInquiryRow(
            order_number=row.order_number,
            symbol=row.symbol_code,
            quantity=row.executed_quantity,
            status=resolve_order_status(row),
        )
        for row in rows
    )


def run_order_inquiry_test(
    *,
    settings: AppSettings,
    start_date: str | None = None,
    end_date: str | None = None,
    symbol_code: str = "",
    registry: ApiRegistry | None = None,
    rest_client: KisRestClient | None = None,
    rest_transport: RestHttpTransport | None = None,
) -> OrderInquiryTestResult:
    """Fetch daily order/execution history via KisRestClient and ApiRegistry."""
    error = vts_common.validate_simulation_environment(settings, require_account=True)
    if error is not None:
        return OrderInquiryTestResult(
            rt_cd="1",
            msg_cd="CONFIG",
            msg1=error,
            order_count=0,
        )

    try:
        inquiry_start, inquiry_end = default_inquiry_date_range()
        inquiry_start = start_date or inquiry_start
        inquiry_end = end_date or inquiry_end
        account = build_account_context(settings)
        api_registry = registry or ApiRegistry.default()
        resolver = build_account_api_resolver(api_registry, use_mock_tr_id=settings.is_mock_account)
        resolved = resolver.resolve(INQUIRE_DAILY_CCLD)
        client = rest_client or build_account_rest_client(settings, transport=rest_transport)
        request = TradeHistoryRequestDto(
            account=account,
            start_date=inquiry_start,
            end_date=inquiry_end,
            symbol_code=symbol_code,
        )
        result = client.get(
            resolved.path,
            resolved.tr_id,
            params=request.to_params(),
            raise_on_error=False,
        )
        rows = TradeHistoryDto.from_api_output1(result.output1)
        orders = to_order_rows(rows)
        return OrderInquiryTestResult(
            rt_cd=result.rt_cd,
            msg_cd=result.msg_cd,
            msg1=vts_common.mask_text(result.msg1),
            order_count=len(orders),
            orders=orders,
        )
    except Exception as exc:  # noqa: BLE001 - surface masked error to CLI
        return OrderInquiryTestResult(
            rt_cd="1",
            msg_cd="ERROR",
            msg1=vts_common.mask_text(str(exc)),
            order_count=0,
        )


def print_result(result: OrderInquiryTestResult) -> None:
    """Print inquiry summary and order rows without sensitive values."""
    print(f"rt_cd: {result.rt_cd}")
    print(f"msg_cd: {result.msg_cd}")
    print(f"msg1: {result.msg1}")
    print(f"order_count: {result.order_count}")
    for order in result.orders:
        print(f"order_number: {order.order_number}")
        print(f"symbol: {order.symbol}")
        print(f"quantity: {order.quantity}")
        print(f"status: {order.status}")


def main() -> int:
    """Run the daily order/execution inquiry test."""
    logging.basicConfig(level=logging.WARNING)
    root = project_root()
    settings = load_simulation_settings(root)
    result = run_order_inquiry_test(settings=settings)
    print_result(result)
    return 0 if result.rt_cd == "0" else 1


if __name__ == "__main__":
    sys.exit(main())
