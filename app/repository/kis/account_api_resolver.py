"""Account API resolver using shared KisApiResolver."""

from __future__ import annotations

from app.broker.kis.api import ApiRegistry
from app.broker.kis.api.account_api_keys import ACCOUNT_API_KEYS
from app.repository.kis.kis_api_resolver import KisApiResolver, ResolvedKisApi

AccountApiResolver = KisApiResolver
ResolvedAccountApi = ResolvedKisApi


def build_account_api_resolver(
    registry: ApiRegistry,
    *,
    use_mock_tr_id: bool = True,
) -> KisApiResolver:
    """Create an account API resolver."""
    return KisApiResolver(
        registry,
        ACCOUNT_API_KEYS,
        use_mock_tr_id=use_mock_tr_id,
    )
