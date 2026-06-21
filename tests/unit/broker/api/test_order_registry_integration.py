"""Registry integration tests for order APIs."""

from __future__ import annotations

import pytest

from app.broker.kis.api import ApiRegistry, HttpMethod
from app.broker.kis.api.order_api_keys import ORDER_CASH, ORDER_RVSECNL

pytestmark = pytest.mark.unit


class TestOrderRegistryIntegration:
    """Integration tests for order API registry entries."""

    def test_order_cash_registered(self) -> None:
        registry = ApiRegistry.default()
        metadata = registry.endpoints.get_by_key(ORDER_CASH)

        assert metadata is not None
        assert metadata.requires_hashkey is True
        assert metadata.method == HttpMethod.POST
        assert metadata.tr_id == "TTTC0012U"

    def test_order_rvsecncl_registered(self) -> None:
        registry = ApiRegistry.default()
        metadata = registry.endpoints.get_by_key(ORDER_RVSECNL)

        assert metadata is not None
        assert metadata.requires_hashkey is True
        assert metadata.tr_id == "TTTC0013U"

    def test_mock_tr_ids_registered(self) -> None:
        registry = ApiRegistry.default()

        assert registry.tr_ids.get("VTTC0012U") is not None
        assert registry.tr_ids.get("VTTC0013U") is not None
