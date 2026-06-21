"""Shared fixtures for strategy tests."""

from __future__ import annotations

from app.service.strategy.strategy_service import StrategyService
from tests.fixtures.event_fixtures import build_test_event_bus_service


def build_test_strategy_service(*, with_event_bus: bool = False) -> StrategyService | tuple:
    """Build StrategyService, optionally wired to EventBus."""
    if not with_event_bus:
        return StrategyService()
    event_bus = build_test_event_bus_service()
    service = StrategyService(event_bus=event_bus)
    service.start(event_bus)
    return service, event_bus


def sample_market_data_payload(*, symbol: str = "005930", price: str = "70000") -> dict:
    """Sample MarketDataEvent payload."""
    return {"symbol_code": symbol, "price": price}


def register_and_start_strategy(
    service: StrategyService,
    *,
    strategy_type: str,
    name: str,
    symbols: list[str] | None = None,
    parameters: dict | None = None,
) -> str:
    """Register and start a strategy, returning its ID."""
    dto = service.register_strategy(
        strategy_type=strategy_type,
        name=name,
        symbols=symbols or ["005930"],
        parameters=parameters or {},
        auto_start=True,
    )
    return dto.strategy_id
