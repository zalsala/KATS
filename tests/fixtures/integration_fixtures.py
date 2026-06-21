"""Shared fixtures for integration tests."""

from __future__ import annotations

import json
from pathlib import Path

from app.bootstrap.application_bootstrap import ApplicationBootstrap, BootstrapOptions
from app.context.application_context import ApplicationContext
from tests.fixtures.auth_fixtures import MockHttpTransport
from tests.fixtures.ws_fixtures import MockWsTransport


def prepare_integration_root(tmp_path: Path, source_root: Path) -> Path:
    """Copy minimal project assets into a temporary integration root."""
    import shutil

    shutil.copytree(source_root / "config", tmp_path / "config")
    shutil.copytree(source_root / "plugins", tmp_path / "plugins")
    return tmp_path


def write_user_settings(root: Path, payload: dict[str, object]) -> None:
    """Write merged user settings overrides."""
    settings_path = root / "data" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(payload), encoding="utf-8")


def build_integration_context(
    root: Path,
    *,
    ws_transport: MockWsTransport | None = None,
    enable_ui_notifications: bool = False,
) -> ApplicationContext:
    """Bootstrap an ApplicationContext for integration tests."""
    if ws_transport is not None:
        env_path = root / ".env"
        env_path.write_text(
            "KATS_ENV=development\nKIS_APP_KEY=test-key\nKIS_APP_SECRET=test-secret\n",
            encoding="utf-8",
        )
    auth_transport = MockHttpTransport() if ws_transport is not None else None
    bootstrap = ApplicationBootstrap(
        root,
        environment="development",
        options=BootstrapOptions(
            setup_logging=True,
            validate_runtime=False,
            enable_ui_notifications=enable_ui_notifications,
            ws_transport=ws_transport,
            auth_transport=auth_transport,
        ),
    )
    context = bootstrap.bootstrap()
    if ws_transport is not None and context.authentication is not None:
        context.authentication.token_manager.issue()
        context.authentication.approval_key_manager.issue()
    return context
