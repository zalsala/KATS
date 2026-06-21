"""KIS current price inquiry test for simulation (VTS) environment."""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from pathlib import Path

SAMSUNG_SYMBOL = "005930"


def _bootstrap_import_path() -> None:
    """Allow ``python scripts/test_current_price.py`` from the project root."""
    root = Path(__file__).resolve().parents[1]
    scripts_dir = Path(__file__).resolve().parent
    for path_str in (str(root), str(scripts_dir)):
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


_bootstrap_import_path()

import vts_common  # noqa: E402

from app.broker.kis.api import ApiRegistry  # noqa: E402
from app.broker.kis.api.market_api_keys import INQUIRE_PRICE  # noqa: E402
from app.broker.kis.rest.http_transport import RestHttpTransport  # noqa: E402
from app.broker.kis.rest.kis_rest_client import KisRestClient  # noqa: E402
from app.config.app_settings import AppSettings  # noqa: E402
from app.dto.market.inquire_price_dto import (  # noqa: E402
    InquirePriceRequestDto,
    InquirePriceResponseDto,
)
from app.repository.kis.market_api_resolver import MarketApiResolver  # noqa: E402

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CurrentPriceTestResult:
    """Normalized current price inquiry response for CLI output."""

    rt_cd: str
    msg_cd: str
    msg1: str
    current_price: str


project_root = vts_common.project_root
load_simulation_settings = vts_common.load_simulation_settings
build_market_rest_client = vts_common.build_rest_client


def run_current_price_test(
    *,
    settings: AppSettings,
    symbol_code: str = SAMSUNG_SYMBOL,
    registry: ApiRegistry | None = None,
    rest_client: KisRestClient | None = None,
    rest_transport: RestHttpTransport | None = None,
) -> CurrentPriceTestResult:
    """Fetch current price via KisRestClient and ApiRegistry without hardcoded TR IDs."""
    error = vts_common.validate_simulation_environment(settings)
    if error is not None:
        return CurrentPriceTestResult(
            rt_cd="1",
            msg_cd="CONFIG",
            msg1=error,
            current_price="",
        )

    try:
        api_registry = registry or ApiRegistry.default()
        resolver = MarketApiResolver(api_registry, use_mock_tr_id=settings.is_mock_account)
        resolved = resolver.resolve(INQUIRE_PRICE)
        client = rest_client or build_market_rest_client(settings, transport=rest_transport)
        request = InquirePriceRequestDto(fid_input_iscd=symbol_code)
        result = client.get(
            resolved.path,
            resolved.tr_id,
            params=request.to_params(),
            raise_on_error=False,
        )
        response = InquirePriceResponseDto.from_api_output(result.output)
        return CurrentPriceTestResult(
            rt_cd=result.rt_cd,
            msg_cd=result.msg_cd,
            msg1=vts_common.mask_text(result.msg1),
            current_price=response.current_price,
        )
    except Exception as exc:  # noqa: BLE001 - surface masked error to CLI
        return CurrentPriceTestResult(
            rt_cd="1",
            msg_cd="ERROR",
            msg1=vts_common.mask_text(str(exc)),
            current_price="",
        )


def print_result(result: CurrentPriceTestResult) -> None:
    """Print KIS response summary without token values."""
    print(f"rt_cd: {result.rt_cd}")
    print(f"msg_cd: {result.msg_cd}")
    print(f"msg1: {result.msg1}")
    print(f"current_price: {result.current_price}")


def main() -> int:
    """Run the Samsung Electronics current price inquiry test."""
    logging.basicConfig(level=logging.WARNING)
    root = project_root()
    settings = load_simulation_settings(root)
    result = run_current_price_test(settings=settings, symbol_code=SAMSUNG_SYMBOL)
    print_result(result)
    return 0 if result.rt_cd == "0" else 1


if __name__ == "__main__":
    sys.exit(main())
