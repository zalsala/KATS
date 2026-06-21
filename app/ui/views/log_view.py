"""Log view."""

from __future__ import annotations

from PySide6.QtWidgets import QPlainTextEdit, QVBoxLayout, QWidget

from app.ui.viewmodels.main_view_model import MainViewModel
from app.ui.views.view_base import bind_view_model


class LogView(QWidget):
    """Log output panel."""

    def __init__(self, *, view_model: MainViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = view_model.log
        self._text = QPlainTextEdit()
        self._text.setReadOnly(True)

        layout = QVBoxLayout(self)
        layout.addWidget(self._text)
        bind_view_model(self._vm, lambda _field: self.refresh())

    def refresh(self) -> None:
        lines = [
            f"[{entry.timestamp.isoformat()}] {entry.level}: {entry.message}"
            for entry in self._vm.entries
        ]
        self._text.setPlainText("\n".join(lines))
