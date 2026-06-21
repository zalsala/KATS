"""VTS mock buy order test for simulation environment."""

from __future__ import annotations

import logging
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

SAMSUNG_SYMBOL = "005930"
ORDER_QUANTITY = "1"
ORDER_DIVISION_LIMIT = "00"
LIMIT_PRICE_OFFSET = 100
CONFIRMATION_PROMPT = "VTS 모의 매수 주문 1주를 실행합니다. 계속하려면 YES 입력"


def _bootstrap_import_path() -> None:
    """Allow ``python scripts/test_vts_buy_order.py`` from the project root."""
    root = Path(__file__).resolve().parents[1]
    scripts_dir = Path(__file__).resolve().parent
    for path_str in (str(root), str(scripts_dir)):
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


_bootstrap_import_path()

import vts_common  # noqa: E402

from app.bootstrap.broker_wiring import build_authentication, build_order_service  # noqa: E402
from app.broker.kis.api import ApiRegistry  # noqa: E402
from app.broker.kis.api.market_api_keys import INQUIRE_PRICE  # noqa: E402
from app.broker.kis.rest.http_transport import RestHttpTransport  # noqa: E402
from app.broker.kis.rest.kis_rest_client import KisRestClient  # noqa: E402
from app.config.app_settings import AppSettings  # noqa: E402
from app.config.config_manager import ConfigManager  # noqa: E402
from app.core.constants import KIS_ACCOUNT_MOCK  # noqa: E402
from app.database.database_manager import DatabaseManager  # noqa: E402
from app.dto.market.inquire_price_dto import (  # noqa: E402
    InquirePriceRequestDto,
    InquirePriceResponseDto,
)
from app.dto.order.order_requests import CashBuyOrderRequest  # noqa: E402
from app.repository.kis.market_api_resolver import MarketApiResolver  # noqa: E402
from app.service.order.order_service import OrderService  # noqa: E402

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class VtsBuyOrderTestResult:
    """Normalized VTS buy order response for CLI output."""

    rt_cd: str
    msg_cd: str
    msg1: str
    order_number: str


project_root = vts_common.project_root
load_simulation_settings = vts_common.load_simulation_settings
build_account_context = vts_common.build_account_context
build_market_rest_client = vts_common.build_rest_client


def validate_vts_buy_prerequisites(settings: AppSettings) -> str | None:
    """Return an error message when VTS mock buy prerequisites are not met."""
    error = vts_common.validate_simulation_environment(settings, require_account=True)
    if error is not None:
        return error
    if settings.secrets.account_type != KIS_ACCOUNT_MOCK:
        return "VTS mock account only (KIS_ACCOUNT_TYPE=mock)"
    if settings.config.order.live_trading_enabled:
        return "live_trading_enabled must remain false for this script"
    return None


def fetch_current_price(
    *,
    settings: AppSettings,
    symbol_code: str,
    rest_client: KisRestClient | None = None,
    rest_transport: RestHttpTransport | None = None,
) -> str:
    """Fetch the current price for a symbol via ApiRegistry."""
    api_registry = ApiRegistry.default()
    resolver = MarketApiResolver(api_registry, use_mock_tr_id=settings.is_mock_account)
    resolved = resolver.resolve(INQUIRE_PRICE)
    client = rest_client or build_market_rest_client(settings, transport=rest_transport)
    request = InquirePriceRequestDto(fid_input_iscd=symbol_code)
    result = client.get(
        resolved.path,
        resolved.tr_id,
        params=request.to_params(),
        raise_on_error=True,
    )
    response = InquirePriceResponseDto.from_api_output(result.output)
    if not response.current_price:
        msg = "Current price is missing from KIS response"
        raise ValueError(msg)
    return response.current_price


def calculate_limit_buy_price(current_price: str, *, offset: int = LIMIT_PRICE_OFFSET) -> str:
    """Return a limit buy price below the current price."""
    normalized = int(current_price)
    return str(max(1, normalized - offset))


def prompt_user_confirmation(
    *,
    prompt: str = CONFIRMATION_PROMPT,
    input_func: Callable[[], str] = input,
) -> bool:
    """Require explicit YES confirmation before placing a mock order."""
    print(prompt)
    return input_func().strip() == "YES"


def build_vts_order_service(
    settings: AppSettings,
    *,
    rest_transport: RestHttpTransport | None = None,
) -> OrderService:
    """Wire OrderService with HashKeyManager for VTS mock trading."""
    manager = ConfigManager.get_instance()
    auth = build_authentication(settings, transport=None)
    database_manager = DatabaseManager.from_config_manager(manager)
    return build_order_service(
        settings=settings,
        auth=auth,
        database_manager=database_manager,
        rest_transport=rest_transport,
    )


def run_vts_buy_order_test(
    *,
    settings: AppSettings,
    symbol_code: str = SAMSUNG_SYMBOL,
    quantity: str = ORDER_QUANTITY,
    user_confirmed: bool | None = None,
    current_price: str | None = None,
    order_service: OrderService | None = None,
    rest_transport: RestHttpTransport | None = None,
    price_fetcher: Callable[..., str] | None = None,
) -> VtsBuyOrderTestResult:
    """Place a VTS mock limit buy order via OrderService."""
    prerequisite_error = validate_vts_buy_prerequisites(settings)
    if prerequisite_error is not None:
        return VtsBuyOrderTestResult(
            rt_cd="1",
            msg_cd="CONFIG",
            msg1=prerequisite_error,
            order_number="",
        )

    confirmed = user_confirmed if user_confirmed is not None else prompt_user_confirmation()
    if not confirmed:
        return VtsBuyOrderTestResult(
            rt_cd="1",
            msg_cd="CANCELLED",
            msg1="User did not confirm with YES",
            order_number="",
        )

    try:
        fetch_price = price_fetcher or fetch_current_price
        market_price = current_price or fetch_price(
            settings=settings,
            symbol_code=symbol_code,
            rest_transport=rest_transport,
        )
        limit_price = calculate_limit_buy_price(market_price)
        service = order_service or build_vts_order_service(
            settings,
            rest_transport=rest_transport,
        )
        request = CashBuyOrderRequest(
            account=build_account_context(settings),
            symbol_code=symbol_code,
            quantity=quantity,
            price=limit_price,
            order_division=ORDER_DIVISION_LIMIT,
        )
        result = service.place_cash_buy_order(request)
        return VtsBuyOrderTestResult(
            rt_cd=result.rt_cd,
            msg_cd=result.msg_cd,
            msg1=vts_common.mask_text(result.msg1),
            order_number=result.order_number,
        )
    except Exception as exc:  # noqa: BLE001 - surface masked error to CLI
        return VtsBuyOrderTestResult(
            rt_cd="1",
            msg_cd="ERROR",
            msg1=vts_common.mask_text(str(exc)),
            order_number="",
        )


def print_result(result: VtsBuyOrderTestResult) -> None:
    """Print order response summary without token or account values."""
    print(f"rt_cd: {result.rt_cd}")
    print(f"msg_cd: {result.msg_cd}")
    print(f"msg1: {result.msg1}")
    print(f"order_number: {result.order_number}")


def main() -> int:
    """Run the VTS mock buy order test."""
    logging.basicConfig(level=logging.WARNING)
    root = project_root()
    settings = load_simulation_settings(root)
    result = run_vts_buy_order_test(settings=settings, symbol_code=SAMSUNG_SYMBOL)
    print_result(result)
    if result.msg_cd == "CANCELLED":
        return 2
    return 0 if result.rt_cd == "0" else 1


if __name__ == "__main__":
    sys.exit(main())
