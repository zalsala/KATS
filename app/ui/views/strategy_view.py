"""Strategy view."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.ui.controllers.ui_controller import UiController
from app.ui.viewmodels.main_view_model import MainViewModel
from app.ui.views.view_base import bind_view_model


class StrategyView(QWidget):
    """Strategy registration and control panel."""

    _COLUMNS = ("ID", "Name", "Type", "State", "Symbols")

    def __init__(
        self,
        *,
        view_model: MainViewModel,
        controller: UiController,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._vm = view_model.strategy
        self._controller = controller
        self._name = QLineEdit("ui-strategy")
        self._symbol = QLineEdit("005930")
        self._message = QLineEdit()
        self._message.setReadOnly(True)
        self._table = QTableWidget(0, len(self._COLUMNS))
        self._table.setHorizontalHeaderLabels(list(self._COLUMNS))
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        register_btn = QPushButton("Register Buy&Hold")
        start_btn = QPushButton("Start Selected")
        stop_btn = QPushButton("Stop Selected")
        register_btn.clicked.connect(self._register)
        start_btn.clicked.connect(self._start_selected)
        stop_btn.clicked.connect(self._stop_selected)

        buttons = QHBoxLayout()
        buttons.addWidget(register_btn)
        buttons.addWidget(start_btn)
        buttons.addWidget(stop_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self._name)
        layout.addWidget(self._symbol)
        layout.addLayout(buttons)
        layout.addWidget(self._table)
        layout.addWidget(self._message)
        bind_view_model(self._vm, lambda _field: self.refresh())

    def refresh(self) -> None:
        rows = self._vm.strategies
        self._table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            values = [row.strategy_id, row.name, row.strategy_type, row.state, row.symbols]
            for col_index, value in enumerate(values):
                self._table.setItem(row_index, col_index, QTableWidgetItem(value))
        self._message.setText(self._vm.last_message)

    def _selected_strategy_id(self) -> str | None:
        row = self._table.currentRow()
        if row < 0:
            return None
        item = self._table.item(row, 0)
        return item.text() if item else None

    def _register(self) -> None:
        dto = self._controller.register_strategy(
            strategy_type="buy_and_hold",
            name=self._name.text().strip() or "ui-strategy",
            symbols=[self._symbol.text().strip() or "005930"],
            parameters={"quantity": "1"},
        )
        self._vm.set_message(f"Registered {dto.strategy_id}")
        self._vm.update_strategies(self._controller.list_strategy_rows())

    def _start_selected(self) -> None:
        strategy_id = self._selected_strategy_id()
        if strategy_id is None:
            self._vm.set_message("Select a strategy")
            return
        dto = self._controller.start_strategy(strategy_id)
        self._vm.set_message(f"Started {dto.name}")
        self._vm.update_strategies(self._controller.list_strategy_rows())

    def _stop_selected(self) -> None:
        strategy_id = self._selected_strategy_id()
        if strategy_id is None:
            self._vm.set_message("Select a strategy")
            return
        dto = self._controller.stop_strategy(strategy_id)
        self._vm.set_message(f"Stopped {dto.name}")
        self._vm.update_strategies(self._controller.list_strategy_rows())
