"""Seed API metadata aligned with the official KIS OpenAPI repository."""

from __future__ import annotations

from app.broker.kis.api.enums import ApiCategory, HttpMethod
from app.broker.kis.api.metadata import ApiMetadata
from app.core.constants import (
    KIS_HASHKEY_PATH,
    KIS_OAUTH_APPROVAL_PATH,
    KIS_OAUTH_TOKEN_PATH,
)

AUTH_APIS: tuple[ApiMetadata, ...] = (
    ApiMetadata(
        api_key="auth.oauth_token",
        name="OAuth Access Token",
        category=ApiCategory.AUTH,
        method=HttpMethod.POST,
        path=KIS_OAUTH_TOKEN_PATH,
        tr_id="",
        description="Issue OAuth access token via /oauth2/tokenP",
        sub_category="oauth",
    ),
    ApiMetadata(
        api_key="auth.approval_key",
        name="WebSocket Approval Key",
        category=ApiCategory.AUTH,
        method=HttpMethod.POST,
        path=KIS_OAUTH_APPROVAL_PATH,
        tr_id="",
        description="Issue WebSocket approval key via /oauth2/Approval",
        sub_category="oauth",
    ),
    ApiMetadata(
        api_key="auth.hashkey",
        name="Order HashKey",
        category=ApiCategory.AUTH,
        method=HttpMethod.POST,
        path=KIS_HASHKEY_PATH,
        tr_id="",
        description="Generate order HashKey via /uapi/hashkey",
        sub_category="oauth",
        requires_hashkey=False,
    ),
)

DOMESTIC_STOCK_APIS: tuple[ApiMetadata, ...] = (
    ApiMetadata(
        api_key="domestic_stock.inquire_price",
        name="Inquire Price",
        category=ApiCategory.DOMESTIC_STOCK,
        method=HttpMethod.GET,
        path="/uapi/domestic-stock/v1/quotations/inquire-price",
        tr_id="FHKST01010100",
        description="Domestic stock current price inquiry",
        sub_category="quotations",
        enabled=True,
    ),
    ApiMetadata(
        api_key="domestic_stock.inquire_asking_price",
        name="Inquire Asking Price",
        category=ApiCategory.DOMESTIC_STOCK,
        method=HttpMethod.GET,
        path="/uapi/domestic-stock/v1/quotations/inquire-asking-price",
        tr_id="FHKST01010200",
        description="Domestic stock asking price inquiry",
        sub_category="quotations",
        enabled=True,
    ),
    ApiMetadata(
        api_key="domestic_stock.order_cash",
        name="Order Cash",
        category=ApiCategory.DOMESTIC_STOCK,
        method=HttpMethod.POST,
        path="/uapi/domestic-stock/v1/trading/order-cash",
        tr_id="TTTC0012U",
        description="Domestic stock cash order",
        sub_category="trading",
        requires_hashkey=True,
        enabled=True,
    ),
)

OVERSEAS_STOCK_APIS: tuple[ApiMetadata, ...] = (
    ApiMetadata(
        api_key="overseas_stock.inquire_price",
        name="Overseas Inquire Price",
        category=ApiCategory.OVERSEAS_STOCK,
        method=HttpMethod.GET,
        path="/uapi/overseas-price/v1/quotations/price",
        tr_id="HHDFS00000300",
        description="Overseas stock price inquiry",
        sub_category="quotations",
        enabled=False,
    ),
)

DISABLED_CATEGORY_STUBS: tuple[ApiMetadata, ...] = (
    ApiMetadata(
        api_key="domestic_bond.stub",
        name="Domestic Bond Stub",
        category=ApiCategory.DOMESTIC_BOND,
        method=HttpMethod.GET,
        path="/uapi/domestic-bond/v1/quotations/inquire-price",
        tr_id="FHKBP01010100",
        description="Reserved domestic bond category stub",
        sub_category="quotations",
        enabled=False,
    ),
    ApiMetadata(
        api_key="domestic_futureoption.stub",
        name="Domestic FutureOption Stub",
        category=ApiCategory.DOMESTIC_FUTUREOPTION,
        method=HttpMethod.GET,
        path="/uapi/domestic-futureoption/v1/quotations/inquire-price",
        tr_id="FHKFT01010100",
        description="Reserved domestic futureoption category stub",
        sub_category="quotations",
        enabled=False,
    ),
    ApiMetadata(
        api_key="elw.stub",
        name="ELW Stub",
        category=ApiCategory.ELW,
        method=HttpMethod.GET,
        path="/uapi/elw/v1/quotations/inquire-price",
        tr_id="FHKEW01010100",
        description="Reserved ELW category stub",
        sub_category="quotations",
        enabled=False,
    ),
    ApiMetadata(
        api_key="etfetn.stub",
        name="ETF ETN Stub",
        category=ApiCategory.ETFETN,
        method=HttpMethod.GET,
        path="/uapi/etfetn/v1/quotations/inquire-price",
        tr_id="FHKET01010100",
        description="Reserved ETF/ETN category stub",
        sub_category="quotations",
        enabled=False,
    ),
)

ACCOUNT_APIS: tuple[ApiMetadata, ...] = (
    ApiMetadata(
        api_key="account.inquire_balance",
        name="Inquire Account Balance",
        category=ApiCategory.DOMESTIC_STOCK,
        method=HttpMethod.GET,
        path="/uapi/domestic-stock/v1/trading/inquire-balance",
        tr_id="TTTC8434R",
        description="Account balance and holdings inquiry",
        sub_category="trading",
        supports_pagination=True,
        enabled=True,
    ),
    ApiMetadata(
        api_key="account.inquire_psbl_order",
        name="Inquire Orderable Amount",
        category=ApiCategory.DOMESTIC_STOCK,
        method=HttpMethod.GET,
        path="/uapi/domestic-stock/v1/trading/inquire-psbl-order",
        tr_id="TTTC8908R",
        description="Orderable cash and quantity inquiry",
        sub_category="trading",
        enabled=True,
    ),
    ApiMetadata(
        api_key="account.inquire_daily_ccld",
        name="Inquire Daily Trade History",
        category=ApiCategory.DOMESTIC_STOCK,
        method=HttpMethod.GET,
        path="/uapi/domestic-stock/v1/trading/inquire-daily-ccld",
        tr_id="TTTC0081R",
        description="Daily order execution history inquiry",
        sub_category="trading",
        supports_pagination=True,
        enabled=True,
    ),
)

ORDER_APIS: tuple[ApiMetadata, ...] = (
    ApiMetadata(
        api_key="order.order_rvsecncl",
        name="Order Revise Cancel",
        category=ApiCategory.DOMESTIC_STOCK,
        method=HttpMethod.POST,
        path="/uapi/domestic-stock/v1/trading/order-rvsecncl",
        tr_id="TTTC0013U",
        description="Domestic stock order modify and cancel",
        sub_category="trading",
        requires_hashkey=True,
        enabled=True,
    ),
)

DEFAULT_API_METADATA: tuple[ApiMetadata, ...] = (
    *AUTH_APIS,
    *DOMESTIC_STOCK_APIS,
    *ACCOUNT_APIS,
    *ORDER_APIS,
    *OVERSEAS_STOCK_APIS,
    *DISABLED_CATEGORY_STUBS,
)
