"""KIS orderable amount inquiry test for simulation (VTS) environment."""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from pathlib import Path

SAMSUNG_SYMBOL = "005930"
ORDER_DIVISION_LIMIT = "00"
TEST_ORDER_UNIT_PRICE = "70000"
BUY_ORDER_QUANTITY = "1"


def _bootstrap_import_path() -> None:
    """Allow ``python scripts/test_orderable_amount.py`` from the project root."""
    root = Path(__file__).resolve().parents[1]
    scripts_dir = Path(__file__).resolve().parent
    for path_str in (str(root), str(scripts_dir)):
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


_bootstrap_import_path()

import vts_common  # noqa: E402

from app.broker.kis.api import ApiRegistry  # noqa: E402
from app.broker.kis.api.account_api_keys import INQUIRE_PSBL_ORDER  # noqa: E402
from app.broker.kis.rest.http_transport import RestHttpTransport  # noqa: E402
from app.broker.kis.rest.kis_rest_client import KisRestClient  # noqa: E402
from app.config.app_settings import AppSettings  # noqa: E402
from app.dto.account.orderable_amount_dto import (  # noqa: E402
    OrderableAmountDto,
    OrderableAmountRequestDto,
)
from app.repository.kis.account_api_resolver import build_account_api_resolver  # noqa: E402

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class OrderableAmountTestResult:
    """Normalized orderable amount inquiry response for CLI output."""

    rt_cd: str
    msg_cd: str
    msg1: str
    orderable_amount: str


project_root = vts_common.project_root
load_simulation_settings = vts_common.load_simulation_settings
build_account_context = vts_common.build_account_context
build_account_rest_client = vts_common.build_rest_client


def run_orderable_amount_test(
    *,
    settings: AppSettings,
    symbol_code: str = SAMSUNG_SYMBOL,
    registry: ApiRegistry | None = None,
    rest_client: KisRestClient | None = None,
    rest_transport: RestHttpTransport | None = None,
) -> OrderableAmountTestResult:
    """Fetch orderable amount via KisRestClient and ApiRegistry without placing orders."""
    error = vts_common.validate_simulation_environment(settings, require_account=True)
    if error is not None:
        return OrderableAmountTestResult(
            rt_cd="1",
            msg_cd="CONFIG",
            msg1=error,
            orderable_amount="",
        )

    try:
        account = build_account_context(settings)
        api_registry = registry or ApiRegistry.default()
        resolver = build_account_api_resolver(api_registry, use_mock_tr_id=settings.is_mock_account)
        resolved = resolver.resolve(INQUIRE_PSBL_ORDER)
        client = rest_client or build_account_rest_client(settings, transport=rest_transport)
        request = OrderableAmountRequestDto(
            account=account,
            symbol_code=symbol_code,
            price=TEST_ORDER_UNIT_PRICE,
            order_division=ORDER_DIVISION_LIMIT,
            quantity=BUY_ORDER_QUANTITY,
        )
        result = client.get(
            resolved.path,
            resolved.tr_id,
            params=request.to_params(),
            raise_on_error=False,
        )
        response = OrderableAmountDto.from_api_output(result.output)
        return OrderableAmountTestResult(
            rt_cd=result.rt_cd,
            msg_cd=result.msg_cd,
            msg1=vts_common.mask_text(result.msg1),
            orderable_amount=response.orderable_cash,
        )
    except Exception as exc:  # noqa: BLE001 - surface masked error to CLI
        return OrderableAmountTestResult(
            rt_cd="1",
            msg_cd="ERROR",
            msg1=vts_common.mask_text(str(exc)),
            orderable_amount="",
        )


def print_result(result: OrderableAmountTestResult) -> None:
    """Print KIS response summary without token or account values."""
    print(f"rt_cd: {result.rt_cd}")
    print(f"msg_cd: {result.msg_cd}")
    print(f"msg1: {result.msg1}")
    print(f"orderable_amount: {result.orderable_amount}")


def main() -> int:
    """Run the Samsung Electronics buy-side orderable amount inquiry test."""
    logging.basicConfig(level=logging.WARNING)
    root = project_root()
    settings = load_simulation_settings(root)
    result = run_orderable_amount_test(
        settings=settings,
        symbol_code=SAMSUNG_SYMBOL,
    )
    print_result(result)
    return 0 if result.rt_cd == "0" else 1


if __name__ == "__main__":
    sys.exit(main())
