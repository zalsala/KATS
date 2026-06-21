"""Launch the KATS desktop UI."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.ui.context.ui_app_context import UiAppContext
from app.ui.ui_session import UiSession
from app.ui.windows.main_window import MainWindow


def launch_ui(*, project_root: Path | None = None) -> int:
    """Create and run the desktop application."""
    app = QApplication(sys.argv)
    context = UiAppContext.create(project_root=project_root)
    session = UiSession(context=context)
    session.start()
    window = MainWindow(session=session)
    window.show()
    return app.exec()


def main() -> int:
    """Entry point for UI mode."""
    return launch_ui(project_root=Path.cwd())


if __name__ == "__main__":
    raise SystemExit(main())
