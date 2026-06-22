"""Broker client wiring for application bootstrap."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.broker.kis.api import ApiRegistry
from app.broker.kis.auth import AuthenticationComponents, build_authentication_components
from app.broker.kis.rest.kis_rest_client import build_kis_rest_client
from app.broker.kis.websocket.kis_ws_client import KisWebSocketClient
from app.broker.kis.websocket.production_ws_transport import build_production_ws_transport
from app.broker.kis.websocket.reconnect_manager import ReconnectManager
from app.broker.kis.websocket.subscription_manager import SubscriptionManager
from app.broker.kis.websocket.ws_transport import WsTransport
from app.order.kis_order_api_client import KisOrderApiClient
from app.repository.kis.account_api_client import AccountApiClient
from app.repository.kis.account_api_resolver import build_account_api_resolver
from app.repository.kis.kis_account_repository import KisAccountRepository
from app.service.account.account_service import AccountService, build_account_service
from app.service.order.order_service import OrderService
from app.service.websocket.websocket_service import WebSocketService, build_websocket_service

if TYPE_CHECKING:
    from app.broker.kis.auth.http_transport import HttpTransport
    from app.broker.kis.rest.http_transport import RestHttpTransport
    from app.config.app_settings import AppSettings
    from app.database.database_manager import DatabaseManager


def build_authentication(
    settings: AppSettings,
    *,
    transport: HttpTransport | None = None,
) -> AuthenticationComponents:
    """Build KIS authentication components from settings."""
    return build_authentication_components(settings, transport=transport)


def build_order_service(
    *,
    settings: AppSettings,
    auth: AuthenticationComponents,
    database_manager: DatabaseManager,
    rest_transport: RestHttpTransport | None = None,
) -> OrderService:
    """Wire OrderService with KIS REST client and optional SQLite repository."""
    database_manager.initialize()
    rest_client = build_kis_rest_client(
        broker_config=settings.config.broker,
        token_manager=auth.token_manager,
        header_builder=auth.header_builder,
        transport=rest_transport,
        is_vts=settings.is_mock_account,
    )
    api_client = KisOrderApiClient(
        rest_client=rest_client,
        registry=ApiRegistry.default(),
        hashkey_manager=auth.hashkey_manager,
        use_mock_tr_id=settings.is_mock_account,
    )
    return OrderService(
        order_api_client=api_client,
        order_repository=database_manager.build_order_repository(),
    )


def build_account_service_from_settings(
    *,
    settings: AppSettings,
    auth: AuthenticationComponents,
    rest_transport: RestHttpTransport | None = None,
) -> AccountService:
    """Wire AccountService with KIS REST client and balance inquiry APIs."""
    rest_client = build_kis_rest_client(
        broker_config=settings.config.broker,
        token_manager=auth.token_manager,
        header_builder=auth.header_builder,
        transport=rest_transport,
        is_vts=settings.is_mock_account,
    )
    api_client = AccountApiClient(
        rest_client=rest_client,
        api_resolver=build_account_api_resolver(
            ApiRegistry.default(),
            use_mock_tr_id=settings.is_mock_account,
        ),
    )
    repository = KisAccountRepository(account_api_client=api_client)
    return build_account_service(account_repository=repository)


def build_websocket_service_from_settings(
    *,
    settings: AppSettings,
    auth: AuthenticationComponents,
    ws_transport: WsTransport | None = None,
) -> WebSocketService:
    """Wire WebSocketService without connecting."""
    transport = ws_transport or build_production_ws_transport()
    client = KisWebSocketClient(
        websocket_url=settings.kis_websocket_url,
        transport=transport,
        approval_key_manager=auth.approval_key_manager,
        header_builder=auth.header_builder,
        subscription_manager=SubscriptionManager(),
        reconnect_manager=ReconnectManager(),
    )
    return build_websocket_service(ws_client=client)
