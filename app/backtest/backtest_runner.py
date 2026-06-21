"""Backtest run orchestrator."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from app.backtest.backtest_engine import BacktestEngine
from app.backtest.backtest_portfolio import BacktestPortfolio
from app.backtest.historical_data_provider import HistoricalDataProvider
from app.backtest.market_replay_engine import MarketReplayEngine
from app.backtest.performance_analyzer import PerformanceAnalyzer
from app.backtest.virtual_order_executor import VirtualOrderExecutor
from app.domain.backtest.backtest_result import BacktestResult
from app.domain.risk.risk_policy import RiskPolicy
from app.events.event_bus_service import EventBusService
from app.events.in_memory_event_bus import InMemoryEventBus
from app.service.portfolio.portfolio_service import PortfolioService
from app.service.risk.risk_service import RiskService
from app.service.strategy.strategy_service import StrategyService


@dataclass(frozen=True, slots=True)
class BacktestConfig:
    """Backtest runtime configuration."""

    default_initial_capital: Decimal = Decimal("10000000")


@dataclass(frozen=True, slots=True)
class BacktestRunRequest:
    """Input parameters for a backtest run."""

    provider: HistoricalDataProvider
    strategy_type: str
    strategy_name: str
    symbols: list[str]
    parameters: dict[str, Any]
    initial_capital: Decimal
    risk_policy: RiskPolicy | None = None


class BacktestRunner:
    """Builds runtime components and executes a backtest."""

    def __init__(self, *, config: BacktestConfig | None = None) -> None:
        self._config = config or BacktestConfig()

    def run(self, request: BacktestRunRequest) -> BacktestResult:
        """Run a backtest with the given request."""
        event_bus = EventBusService(event_bus=InMemoryEventBus())
        initial_capital = request.initial_capital

        portfolio_service = PortfolioService(event_bus=event_bus, account_no="backtest")
        portfolio_service.start(event_bus)

        strategy_service = StrategyService(event_bus=event_bus)
        strategy_service.start(event_bus)
        strategy_service.register_strategy(
            strategy_type=request.strategy_type,
            name=request.strategy_name,
            symbols=request.symbols,
            parameters=request.parameters,
            auto_start=True,
        )

        risk_policy = request.risk_policy or RiskPolicy.default()
        risk_service = RiskService(
            portfolio_service=portfolio_service,
            event_bus=event_bus,
            policy=risk_policy,
        )
        risk_service.start(event_bus)

        analyzer = PerformanceAnalyzer(initial_capital=initial_capital)
        backtest_portfolio = BacktestPortfolio(portfolio_service=portfolio_service)
        virtual_executor = VirtualOrderExecutor(
            portfolio=backtest_portfolio,
            analyzer=analyzer,
            event_bus=event_bus,
        )
        virtual_executor.register(event_bus)

        replay_engine = MarketReplayEngine(provider=request.provider, event_bus=event_bus)
        engine = BacktestEngine(
            portfolio_service=portfolio_service,
            strategy_service=strategy_service,
            risk_service=risk_service,
            backtest_portfolio=backtest_portfolio,
            virtual_executor=virtual_executor,
            analyzer=analyzer,
            replay_engine=replay_engine,
            provider=request.provider,
        )

        try:
            return engine.run(initial_capital=initial_capital)
        finally:
            virtual_executor.unregister(event_bus)
            risk_service.stop(event_bus)
            strategy_service.stop(event_bus)
            portfolio_service.stop(event_bus)
