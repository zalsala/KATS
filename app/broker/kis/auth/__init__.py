"""Factory helpers for KIS authentication components."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.broker.kis.auth.approval_key_manager import ApprovalKeyManager
from app.broker.kis.auth.authentication_client import AuthenticationClient
from app.broker.kis.auth.hashkey_manager import HashKeyManager
from app.broker.kis.auth.header_builder import HeaderBuilder
from app.broker.kis.auth.http_transport import HttpTransport
from app.broker.kis.auth.token_cache import TokenCache
from app.broker.kis.auth.token_manager import TokenManager
from app.config.app_settings import AppSettings


@dataclass(frozen=True, slots=True)
class AuthenticationComponents:
    """Bundle of KIS authentication layer objects.

    Attributes:
        auth_client: Low-level authentication HTTP client.
        token_cache: Token and approval key cache.
        token_manager: Access token lifecycle manager.
        approval_key_manager: WebSocket approval key manager.
        hashkey_manager: Order hash key manager.
        header_builder: REST header builder.
    """

    auth_client: AuthenticationClient
    token_cache: TokenCache
    token_manager: TokenManager
    approval_key_manager: ApprovalKeyManager
    hashkey_manager: HashKeyManager
    header_builder: HeaderBuilder


def build_authentication_components(
    settings: AppSettings,
    *,
    token_path: Path | None = None,
    transport: HttpTransport | None = None,
) -> AuthenticationComponents:
    """Create authentication components from application settings.

    Args:
        settings: Loaded application settings.
        token_path: Optional override for token cache path.
        transport: Optional HTTP transport for testing.

    Returns:
        Fully wired authentication component bundle.
    """
    auth_config = settings.config.authentication.model_copy(
        update={
            "app_key": settings.secrets.app_key,
            "app_secret": settings.secrets.app_secret,
            "account_no": settings.secrets.account_no,
            "account_type": settings.secrets.account_type,
        }
    )
    resolved_token_path = token_path or settings.resolve_path(auth_config.token_path)

    auth_client = AuthenticationClient(
        base_url=settings.kis_rest_base_url,
        transport=transport,
    )
    token_cache = TokenCache(token_path=resolved_token_path)
    header_builder = HeaderBuilder(
        app_key=auth_config.app_key,
        app_secret=auth_config.app_secret,
    )
    token_manager = TokenManager(
        auth_config=auth_config,
        auth_client=auth_client,
        token_cache=token_cache,
    )
    approval_key_manager = ApprovalKeyManager(
        auth_config=auth_config,
        auth_client=auth_client,
        token_cache=token_cache,
        token_manager=token_manager,
    )
    hashkey_manager = HashKeyManager(
        auth_client=auth_client,
        token_manager=token_manager,
        header_builder=header_builder,
    )
    return AuthenticationComponents(
        auth_client=auth_client,
        token_cache=token_cache,
        token_manager=token_manager,
        approval_key_manager=approval_key_manager,
        hashkey_manager=hashkey_manager,
        header_builder=header_builder,
    )


__all__ = [
    "ApprovalKeyManager",
    "AuthenticationClient",
    "AuthenticationComponents",
    "HashKeyManager",
    "HeaderBuilder",
    "TokenCache",
    "TokenManager",
    "build_authentication_components",
]
