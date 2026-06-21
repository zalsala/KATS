"""Order view."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.ui.controllers.ui_controller import UiController
from app.ui.models.display_models import OrderFormData
from app.ui.viewmodels.main_view_model import MainViewModel
from app.ui.views.view_base import bind_view_model


class OrderView(QWidget):
    """Order entry form."""

    def __init__(
        self,
        *,
        view_model: MainViewModel,
        controller: UiController,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._vm = view_model.order
        self._controller = controller
        self._symbol = QLineEdit("005930")
        self._quantity = QLineEdit("1")
        self._price = QLineEdit("70000")
        self._side = QComboBox()
        self._side.addItems(["buy", "sell"])
        self._result = QLabel("")
        self._submit = QPushButton("Submit Order")
        self._submit.clicked.connect(self._on_submit)

        form = QFormLayout()
        form.addRow("Symbol", self._symbol)
        form.addRow("Quantity", self._quantity)
        form.addRow("Price", self._price)
        form.addRow("Side", self._side)
        form.addRow("Result", self._result)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self._submit)
        bind_view_model(self._vm, lambda _field: self.refresh())

    def refresh(self) -> None:
        self._result.setText(self._vm.last_message)

    def _on_submit(self) -> None:
        form = OrderFormData(
            symbol_code=self._symbol.text().strip(),
            quantity=self._quantity.text().strip(),
            price=self._price.text().strip(),
            side=self._side.currentText(),
        )
        errors = self._vm.validate_form(form)
        if errors:
            self._vm.set_result(success=False, message=",".join(errors))
            return
        try:
            result = self._controller.submit_order(form)
            message = result.msg1 or result.order_number
            self._vm.set_result(success=result.success, message=message)
        except Exception as exc:
            self._vm.set_result(success=False, message=str(exc))
