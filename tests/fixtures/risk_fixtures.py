"""Shared fixtures for risk tests."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from app.domain.risk.risk_policy import RiskPolicy
from app.domain.strategy.trading_signal import SignalType, TradingSignal
from app.service.portfolio.portfolio_service import PortfolioService
from app.service.risk.risk_service import RiskService
from tests.fixtures.event_fixtures import build_test_event_bus_service
from tests.fixtures.portfolio_fixtures import sample_account_payload


def build_test_risk_policy(**overrides) -> RiskPolicy:
    """Build a strict risk policy for tests."""
    defaults = {
        "max_order_amount": Decimal("1000000"),
        "max_order_quantity": Decimal("100"),
        "max_position_count": 3,
        "max_symbol_weight": Decimal("0.50"),
        "daily_loss_limit": Decimal("0.10"),
        "duplicate_order_block": True,
        "emergency_stop": False,
    }
    defaults.update(overrides)
    return RiskPolicy(**defaults)


def build_test_portfolio_service(*, account_no: str = "12345678") -> PortfolioService:
    """Build portfolio service with sample account."""
    service = PortfolioService(account_no=account_no)
    service.apply_account(sample_account_payload(account_no=account_no))
    return service


def build_test_risk_service(
    *,
    with_event_bus: bool = False,
    policy: RiskPolicy | None = None,
) -> RiskService | tuple:
    """Build RiskService, optionally wired to EventBus."""
    portfolio_service = build_test_portfolio_service()
    if not with_event_bus:
        return RiskService(portfolio_service=portfolio_service, policy=policy)
    event_bus = build_test_event_bus_service()
    service = RiskService(
        portfolio_service=portfolio_service,
        event_bus=event_bus,
        policy=policy,
    )
    service.start(event_bus)
    return service, event_bus


def build_test_buy_signal(**overrides) -> TradingSignal:
    """Build a sample BUY signal."""
    defaults = {
        "signal_id": "sig-001",
        "strategy_id": "strat-001",
        "strategy_name": "test-strategy",
        "symbol_code": "005930",
        "signal_type": SignalType.BUY,
        "price": Decimal("70000"),
        "quantity": Decimal("1"),
        "confidence": Decimal("1"),
        "timestamp": datetime.now(UTC),
        "reason": "test",
    }
    defaults.update(overrides)
    return TradingSignal(**defaults)


def strategy_payload_from_signal(signal: TradingSignal) -> dict:
    """Convert a trading signal to strategy event payload."""
    return {
        "signal_id": signal.signal_id,
        "strategy_id": signal.strategy_id,
        "strategy_name": signal.strategy_name,
        "symbol_code": signal.symbol_code,
        "signal_type": signal.signal_type.value,
        "price": str(signal.price),
        "quantity": str(signal.quantity),
        "confidence": str(signal.confidence),
        "timestamp": signal.timestamp.isoformat(),
        "message": signal.reason,
    }
