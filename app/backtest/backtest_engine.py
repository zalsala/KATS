"""Backtest orchestration engine."""

from __future__ import annotations

import logging
from decimal import Decimal

from app.backtest.backtest_portfolio import BacktestPortfolio
from app.backtest.historical_data_provider import HistoricalDataProvider
from app.backtest.market_replay_engine import MarketReplayEngine
from app.backtest.performance_analyzer import PerformanceAnalyzer
from app.backtest.virtual_order_executor import VirtualOrderExecutor
from app.domain.backtest.backtest_result import BacktestResult
from app.domain.backtest.historical_bar import HistoricalBar
from app.service.portfolio.portfolio_service import PortfolioService
from app.service.risk.risk_service import RiskService
from app.service.strategy.strategy_service import StrategyService


class BacktestEngine:
    """Coordinates replay, strategy, risk, and virtual execution."""

    def __init__(
        self,
        *,
        portfolio_service: PortfolioService,
        strategy_service: StrategyService,
        risk_service: RiskService,
        backtest_portfolio: BacktestPortfolio,
        virtual_executor: VirtualOrderExecutor,
        analyzer: PerformanceAnalyzer,
        replay_engine: MarketReplayEngine,
        provider: HistoricalDataProvider,
    ) -> None:
        self._portfolio_service = portfolio_service
        self._strategy_service = strategy_service
        self._risk_service = risk_service
        self._backtest_portfolio = backtest_portfolio
        self._virtual_executor = virtual_executor
        self._analyzer = analyzer
        self._replay_engine = replay_engine
        self._provider = provider
        self._logger = logging.getLogger(__name__)

    def run(self, *, initial_capital: Decimal) -> BacktestResult:
        """Execute a full backtest run."""
        self._backtest_portfolio.initialize(initial_capital=initial_capital)
        self._risk_service.manager.clear_all_pending_orders()
        self._risk_service.manager.set_emergency_stop(False)

        def _after_bar(bar: HistoricalBar) -> None:
            snapshot = self._backtest_portfolio.get_snapshot()
            self._analyzer.record_equity(bar.timestamp, snapshot.total_asset)

        replay_count = self._replay_engine.replay(on_after_bar=_after_bar)
        final_snapshot = self._backtest_portfolio.get_snapshot()
        self._logger.info(
            "Backtest finished bars=%s final_asset=%s",
            replay_count,
            final_snapshot.total_asset,
        )
        return self._analyzer.finalize(final_snapshot.total_asset)
