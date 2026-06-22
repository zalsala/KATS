"""Market view."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.ui.controllers.ui_controller import UiController
from app.ui.viewmodels.main_view_model import MainViewModel
from app.ui.views.view_base import bind_view_model
from app.ui.widgets.chart_widget import ChartWidget


class MarketView(QWidget):
    """Market data display panel."""

    def __init__(
        self,
        *,
        view_model: MainViewModel,
        controller: UiController,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._controller = controller
        self._vm = view_model.market
        self._chart_vm = view_model.chart
        self._symbol = QLabel("-")
        self._price = QLabel("-")
        self._updated = QLabel("-")
        self._chart_widget = ChartWidget()
        self._symbol_input = QLineEdit(self._vm.symbol_input)
        self._connect_button = QPushButton("Connect WebSocket")
        self._disconnect_button = QPushButton("Disconnect")
        self._subscribe_button = QPushButton("Subscribe Price")
        self._unsubscribe_button = QPushButton("Unsubscribe")
        self._ws_status = QLabel("-")
        self._sub_status = QLabel("-")
        self._status_message = QLabel("")

        self._symbol_input.textChanged.connect(self._on_symbol_changed)
        self._connect_button.clicked.connect(self._on_connect_clicked)
        self._disconnect_button.clicked.connect(self._on_disconnect_clicked)
        self._subscribe_button.clicked.connect(self._on_subscribe_clicked)
        self._unsubscribe_button.clicked.connect(self._on_unsubscribe_clicked)

        form = QFormLayout()
        form.addRow("Symbol", self._symbol)
        form.addRow("Price", self._price)
        form.addRow("Updated", self._updated)

        controls = QFormLayout()
        controls.addRow("Symbol code", self._symbol_input)

        buttons = QHBoxLayout()
        buttons.addWidget(self._connect_button)
        buttons.addWidget(self._disconnect_button)
        buttons.addWidget(self._subscribe_button)
        buttons.addWidget(self._unsubscribe_button)
        controls.addRow("Controls", buttons)

        controls.addRow("WebSocket", self._ws_status)
        controls.addRow("Subscribed", self._sub_status)
        controls.addRow("Status", self._status_message)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(controls)
        layout.addWidget(self._chart_widget, stretch=1)
        bind_view_model(self._vm, lambda _field: self.refresh())
        bind_view_model(self._chart_vm, lambda _field: self._update_chart_widget())
        self.refresh()
        self._load_chart()

    @property
    def chart_widget(self) -> ChartWidget:
        """Return the embedded chart widget."""
        return self._chart_widget

    def _update_chart_widget(self) -> None:
        self._chart_widget.set_candles(self._chart_vm.candles, symbol=self._chart_vm.symbol_code)

    def refresh(self) -> None:
        """Refresh quote labels and connection state."""
        self._symbol.setText(self._vm.symbol_code or self._chart_vm.symbol_code or "-")
        self._price.setText(str(self._vm.current_price) if self._vm.current_price else "-")
        self._updated.setText(self._vm.last_updated or "-")
        self._ws_status.setText("Connected" if self._vm.websocket_connected else "Disconnected")
        self._sub_status.setText(",".join(sorted(self._vm.subscribed_symbols)) or "-")
        self._status_message.setText(self._vm.status_message or "")

    def _load_chart(self) -> None:
        """Load chart candles from ChartService via ChartViewModel."""
        self._chart_vm.refresh()

    def _normalized_symbol(self) -> str:
        return self._symbol_input.text().strip()

    def _on_symbol_changed(self, text: str) -> None:
        self._vm.set_symbol_input(text.strip())

    def _on_connect_clicked(self) -> None:
        try:
            self._controller.connect_websocket()
            self._vm.set_websocket_connected(True)
            self._vm.set_status_message("WebSocket connected")
        except Exception:
            self._vm.set_websocket_connected(False)
            self._vm.set_status_message("WebSocket connect failed")

    def _on_disconnect_clicked(self) -> None:
        try:
            self._controller.disconnect_websocket()
            self._vm.set_websocket_connected(False)
            self._vm.set_status_message("WebSocket disconnected")
        except Exception:
            self._vm.set_status_message("WebSocket disconnect failed")

    def _on_subscribe_clicked(self) -> None:
        symbol = self._normalized_symbol()
        if not symbol:
            self._vm.set_status_message("Symbol code is required")
            return
        try:
            self._controller.subscribe_realtime_price(symbol)
            self._vm.add_subscription(symbol)
            self._chart_vm.set_symbol(symbol)
            self._vm.set_status_message(f"Subscribed: {symbol}")
        except Exception:
            self._vm.set_status_message("Subscribe failed")

    def _on_unsubscribe_clicked(self) -> None:
        symbol = self._normalized_symbol()
        if not symbol:
            self._vm.set_status_message("Symbol code is required")
            return
        try:
            self._controller.unsubscribe_realtime_price(symbol)
            self._vm.remove_subscription(symbol)
            self._vm.set_status_message(f"Unsubscribed: {symbol}")
        except Exception:
            self._vm.set_status_message("Unsubscribe failed")
