"""Backtest view."""

from __future__ import annotations

from decimal import Decimal

from PySide6.QtWidgets import QFormLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.backtest.sample_data import build_sample_price_provider
from app.ui.controllers.ui_controller import UiController
from app.ui.viewmodels.main_view_model import MainViewModel
from app.ui.views.view_base import bind_view_model


class BacktestView(QWidget):
    """Backtest execution panel."""

    def __init__(
        self,
        *,
        view_model: MainViewModel,
        controller: UiController,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._vm = view_model.backtest
        self._controller = controller
        self._status = QLabel("Idle")
        self._return_rate = QLabel("-")
        self._mdd = QLabel("-")
        self._trades = QLabel("-")
        self._run = QPushButton("Run Sample Backtest")
        self._run.clicked.connect(self._on_run)

        form = QFormLayout()
        form.addRow("Status", self._status)
        form.addRow("Return %", self._return_rate)
        form.addRow("MDD %", self._mdd)
        form.addRow("Trades", self._trades)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self._run)
        bind_view_model(self._vm, lambda _field: self.refresh())

    def refresh(self) -> None:
        self._status.setText("Running" if self._vm.is_running else self._vm.last_message or "Idle")
        if self._vm.last_result is None:
            self._return_rate.setText("-")
            self._mdd.setText("-")
            self._trades.setText("-")
            return
        result = self._vm.last_result
        self._return_rate.setText(str(result.total_return_rate))
        self._mdd.setText(str(result.max_drawdown))
        self._trades.setText(str(result.trade_count))

    def _on_run(self) -> None:
        self._vm.set_running(True)
        try:
            provider = build_sample_price_provider()
            result = self._controller.run_backtest(
                provider=provider,
                strategy_type="buy_and_hold",
                strategy_name="ui-backtest",
                symbols=["005930"],
                parameters={"quantity": "1"},
                initial_capital=Decimal("1000000"),
            )
            display = self._controller.to_backtest_display(result)
            self._vm.set_result(display, message="Completed")
        except Exception as exc:
            self._vm.set_result(None, message=str(exc))
        finally:
            self._vm.set_running(False)
