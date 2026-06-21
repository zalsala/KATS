"""Shared fixtures for portfolio tests."""

from __future__ import annotations

from decimal import Decimal

from app.domain.portfolio.position import Position
from app.portfolio.in_memory_portfolio_store import InMemoryPortfolioStore
from app.portfolio.portfolio_engine import PortfolioEngine
from app.service.portfolio.portfolio_service import PortfolioService
from tests.fixtures.event_fixtures import build_test_event_bus_service


def build_test_position(**overrides) -> Position:
    """Build a sample position for tests."""
    defaults = {
        "symbol_code": "005930",
        "stock_name": "삼성전자",
        "quantity": Decimal("10"),
        "average_price": Decimal("70000"),
        "current_price": Decimal("75000"),
    }
    defaults.update(overrides)
    return Position(**defaults)


def build_test_portfolio_engine(*, account_no: str = "12345678") -> PortfolioEngine:
    """Build PortfolioEngine with in-memory store."""
    store = InMemoryPortfolioStore(account_no=account_no)
    return PortfolioEngine(store=store)


def build_test_portfolio_service(*, account_no: str = "12345678") -> PortfolioService:
    """Build PortfolioService without EventBus."""
    return PortfolioService(account_no=account_no)


def build_test_portfolio_service_with_bus(*, account_no: str = "12345678") -> tuple:
    """Build PortfolioService wired to EventBus."""
    event_bus = build_test_event_bus_service()
    service = PortfolioService(event_bus=event_bus, account_no=account_no)
    service.start(event_bus)
    return service, event_bus


def sample_account_payload(*, account_no: str = "12345678") -> dict:
    """Sample AccountEvent payload."""
    return {
        "account_no": account_no,
        "total_deposit": "1000000",
        "orderable_cash": "800000",
        "holdings": [
            {
                "symbol_code": "005930",
                "stock_name": "삼성전자",
                "quantity": "10",
                "average_price": "70000",
                "current_price": "75000",
            }
        ],
    }
