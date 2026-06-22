"""Market view."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.chart.timeframe import Timeframe
from app.ui.controllers.account_summary_controller import AccountSummaryController
from app.ui.controllers.order_entry_controller import OrderEntryController
from app.ui.controllers.position_controller import PositionController
from app.ui.controllers.ui_controller import UiController
from app.ui.controllers.watchlist_controller import WatchlistController
from app.ui.models.indicator_settings import IndicatorSettings
from app.ui.viewmodels.main_view_model import MainViewModel
from app.ui.views.view_base import bind_view_model
from app.ui.widgets.account_summary_panel import AccountSummaryPanel
from app.ui.widgets.chart_widget import ChartWidget
from app.ui.widgets.order_entry_panel import OrderEntryPanel
from app.ui.widgets.position_panel import PositionPanel
from app.ui.widgets.watchlist_panel import WatchlistPanel


class MarketView(QWidget):
    """Market data display panel."""

    def __init__(
        self,
        *,
        view_model: MainViewModel,
        controller: UiController,
        watchlist_controller: WatchlistController | None = None,
        order_entry_controller: OrderEntryController | None = None,
        position_controller: PositionController | None = None,
        account_summary_controller: AccountSummaryController | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._controller = controller
        self._order_entry_controller = order_entry_controller
        self._position_controller = position_controller
        self._account_summary_controller = account_summary_controller
        self._vm = view_model.market
        self._chart_vm = view_model.chart
        self._watchlist_vm = view_model.watchlist
        self._watchlist_panel: WatchlistPanel | None = None
        self._order_entry_panel: OrderEntryPanel | None = None
        self._position_panel: PositionPanel | None = None
        self._account_summary_panel: AccountSummaryPanel | None = None
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
        self._diag_last_time = QLabel("-")
        self._diag_last_symbol = QLabel("-")
        self._diag_last_price = QLabel("-")
        self._diag_tick_count = QLabel("-")
        self._diag_candle_count = QLabel("-")
        self._timeframe_selector = QComboBox()
        for timeframe in Timeframe:
            self._timeframe_selector.addItem(timeframe.value, timeframe)
        self._timeframe_selector.setCurrentText(self._chart_vm.selected_timeframe.value)
        settings = self._chart_vm.indicator_settings
        self._sma_checkbox = QCheckBox("SMA")
        self._sma_period = QSpinBox()
        self._sma_period.setRange(IndicatorSettings.MIN_PERIOD, IndicatorSettings.MAX_PERIOD)
        self._sma_period.setValue(settings.sma_period)
        self._ema_checkbox = QCheckBox("EMA")
        self._ema_period = QSpinBox()
        self._ema_period.setRange(IndicatorSettings.MIN_PERIOD, IndicatorSettings.MAX_PERIOD)
        self._ema_period.setValue(settings.ema_period)
        self._vwap_checkbox = QCheckBox("VWAP")
        self._sma_checkbox.setChecked(settings.sma_enabled)
        self._ema_checkbox.setChecked(settings.ema_enabled)
        self._vwap_checkbox.setChecked(settings.vwap_enabled)

        self._symbol_input.textChanged.connect(self._on_symbol_changed)
        self._timeframe_selector.currentIndexChanged.connect(self._on_timeframe_changed)
        self._sma_checkbox.toggled.connect(self._on_indicator_settings_changed)
        self._sma_period.valueChanged.connect(self._on_indicator_settings_changed)
        self._ema_checkbox.toggled.connect(self._on_indicator_settings_changed)
        self._ema_period.valueChanged.connect(self._on_indicator_settings_changed)
        self._vwap_checkbox.toggled.connect(self._on_indicator_settings_changed)
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
        controls.addRow("Timeframe", self._timeframe_selector)

        overlays = QHBoxLayout()
        overlays.addWidget(self._sma_checkbox)
        overlays.addWidget(self._sma_period)
        overlays.addWidget(self._ema_checkbox)
        overlays.addWidget(self._ema_period)
        overlays.addWidget(self._vwap_checkbox)
        controls.addRow("Indicators", overlays)

        buttons = QHBoxLayout()
        buttons.addWidget(self._connect_button)
        buttons.addWidget(self._disconnect_button)
        buttons.addWidget(self._subscribe_button)
        buttons.addWidget(self._unsubscribe_button)
        controls.addRow("Controls", buttons)

        controls.addRow("WebSocket", self._ws_status)
        controls.addRow("Subscribed", self._sub_status)
        controls.addRow("Status", self._status_message)

        diagnostics = QFormLayout()
        diagnostics.addRow("Last received", self._diag_last_time)
        diagnostics.addRow("Last symbol", self._diag_last_symbol)
        diagnostics.addRow("Last price", self._diag_last_price)
        diagnostics.addRow("Ticks received", self._diag_tick_count)
        diagnostics.addRow("Candles built", self._diag_candle_count)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(controls)
        layout.addLayout(diagnostics)

        chart_container = QSplitter()
        if watchlist_controller is not None:
            self._watchlist_panel = WatchlistPanel(
                view_model=view_model.watchlist,
                controller=watchlist_controller,
            )
            chart_container.addWidget(self._watchlist_panel)

        chart_column = QSplitter(Qt.Orientation.Vertical)
        chart_column.addWidget(self._chart_widget)
        if account_summary_controller is not None:
            self._account_summary_panel = AccountSummaryPanel(
                view_model=view_model.account_summary,
                controller=account_summary_controller,
            )
            chart_column.addWidget(self._account_summary_panel)
        bottom_row = QSplitter(Qt.Orientation.Horizontal)
        if order_entry_controller is not None:
            self._order_entry_panel = OrderEntryPanel(
                view_model=view_model.order_entry,
                controller=order_entry_controller,
            )
            bottom_row.addWidget(self._order_entry_panel)
        if position_controller is not None:
            self._position_panel = PositionPanel(
                view_model=view_model.position,
                controller=position_controller,
            )
            bottom_row.addWidget(self._position_panel)
        if bottom_row.count() > 0:
            chart_column.addWidget(bottom_row)
        if chart_column.count() > 1:
            chart_column.setStretchFactor(0, 3)
            chart_column.setStretchFactor(chart_column.count() - 1, 1)
        chart_container.addWidget(chart_column)
        chart_container.setStretchFactor(0, 0)
        chart_container.setStretchFactor(1, 1)
        layout.addWidget(chart_container, stretch=1)
        bind_view_model(self._vm, lambda _field: self.refresh())
        bind_view_model(self._chart_vm, lambda field: self._on_chart_changed(field))
        bind_view_model(view_model.watchlist, lambda _field: self._sync_market_symbol())
        self.refresh()
        self._load_chart()

    @property
    def chart_widget(self) -> ChartWidget:
        """Return the embedded chart widget."""
        return self._chart_widget

    @property
    def watchlist_panel(self) -> WatchlistPanel | None:
        """Return the embedded watchlist panel when configured."""
        return self._watchlist_panel

    @property
    def order_entry_panel(self) -> OrderEntryPanel | None:
        """Return the embedded order entry panel when configured."""
        return self._order_entry_panel

    @property
    def position_panel(self) -> PositionPanel | None:
        """Return the embedded position panel when configured."""
        return self._position_panel

    @property
    def account_summary_panel(self) -> AccountSummaryPanel | None:
        """Return the embedded account summary panel when configured."""
        return self._account_summary_panel

    def _on_chart_changed(self, field: str) -> None:
        self._update_chart_widget()
        self._refresh_diagnostics()
        if field in {"candles", "timeframe", "symbol_code"}:
            self._sync_market_symbol()

    def _update_chart_widget(self) -> None:
        self._chart_widget.set_candles(self._chart_vm.candles, symbol=self._chart_vm.symbol_code)
        self._chart_widget.set_indicator_series(self._chart_vm.indicator_series)

    def _refresh_diagnostics(self) -> None:
        self._diag_last_time.setText(self._chart_vm.last_trade_time or "-")
        self._diag_last_symbol.setText(self._chart_vm.last_trade_symbol or "-")
        self._diag_last_price.setText(self._chart_vm.last_trade_price or "-")
        self._diag_tick_count.setText(str(self._chart_vm.total_ticks_received))
        self._diag_candle_count.setText(str(self._chart_vm.total_candles))

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
        self._refresh_diagnostics()

    def _normalized_symbol(self) -> str:
        return self._symbol_input.text().strip()

    def _on_symbol_changed(self, text: str) -> None:
        self._vm.set_symbol_input(text.strip())

    def _on_timeframe_changed(self, _index: int) -> None:
        timeframe = self._timeframe_selector.currentData()
        if timeframe is None:
            return
        self._chart_vm.set_timeframe(timeframe)

    def _on_indicator_settings_changed(self, *_args: object) -> None:
        self._chart_vm.update_indicator_settings(
            IndicatorSettings(
                sma_enabled=self._sma_checkbox.isChecked(),
                sma_period=self._sma_period.value(),
                ema_enabled=self._ema_checkbox.isChecked(),
                ema_period=self._ema_period.value(),
                vwap_enabled=self._vwap_checkbox.isChecked(),
            )
        )

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

    def _sync_market_symbol(self) -> None:
        symbol = (
            self._watchlist_vm.selected_symbol
            or self._chart_vm.symbol_code
            or self._vm.symbol_input
        )
        if not symbol:
            return
        if self._order_entry_controller is not None:
            self._order_entry_controller.sync_symbol(symbol)
        if self._position_controller is not None:
            self._position_controller.sync_selected_symbol(symbol)
