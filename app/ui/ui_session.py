"""UI session wiring."""

from __future__ import annotations

from app.ui.chart_event_bridge import ChartEventBridge
from app.ui.context.ui_app_context import UiAppContext
from app.ui.controllers.ui_controller import UiController
from app.ui.controllers.ui_event_bridge import UiEventBridge
from app.ui.viewmodels.main_view_model import MainViewModel


class UiSession:
    """Wires services, controller, event bridge, and view models."""

    def __init__(self, *, context: UiAppContext) -> None:
        self.context = context
        self.view_model = MainViewModel(chart_service=context.chart_service)
        self.controller = UiController(context=context)
        self.event_bridge = UiEventBridge(controller=self.controller, view_model=self.view_model)
        self.chart_event_bridge = ChartEventBridge(chart_view_model=self.view_model.chart)
        self._started = False

    def start(self) -> None:
        """Start services and UI event subscriptions."""
        if self._started:
            return
        self.context.start()
        self.event_bridge.register(self.context.event_bus)
        self.chart_event_bridge.register(self.context.event_bus)
        self.event_bridge.refresh_all()
        self._started = True

    def stop(self) -> None:
        """Stop UI subscriptions and services."""
        if not self._started:
            return
        self.chart_event_bridge.unregister(self.context.event_bus)
        self.event_bridge.unregister(self.context.event_bus)
        self.context.stop()
        self._started = False
