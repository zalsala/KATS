"""Tests for scripts/test_auth_token.py."""

from __future__ import annotations

import importlib.util
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from tests.fixtures.auth_fixtures import MockHttpTransport, make_kats_config, make_kis_secrets

from app.config.app_settings import AppSettings
from app.core.constants import ENV_SIMULATION, KIS_VTS_REST_BASE_URL

pytestmark = pytest.mark.unit


def _load_module(project_root):
    import sys

    script_path = project_root / "scripts" / "test_auth_token.py"
    module_name = "test_auth_token_script"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _simulation_settings(project_root) -> AppSettings:
    config = make_kats_config()
    config = config.model_copy(update={"environment": ENV_SIMULATION})
    return AppSettings.create(project_root, config, make_kis_secrets())


class TestAuthTokenScript:
    """Tests for the KIS access token test script."""

    def test_project_root(self, project_root) -> None:
        module = _load_module(project_root)
        assert module.project_root() == project_root

    def test_print_credential_diagnostics(self, project_root, capsys) -> None:
        module = _load_module(project_root)
        settings = _simulation_settings(project_root)
        sources = module.SecretSources(
            app_key="env",
            app_secret="env",
            account_no="env",
        )

        module.print_credential_diagnostics(settings, sources)
        output = capsys.readouterr().out

        assert "APP_KEY source: env" in output
        assert "APP_SECRET source: env" in output
        assert "ACCOUNT_NO source: env" in output
        assert "BASE_URL: openapivts..." in output
        assert "ACCOUNT_TYPE: mock" in output
        assert "test-app-key" not in output

    def test_run_token_test_success(self, project_root, capsys) -> None:
        module = _load_module(project_root)
        transport = MockHttpTransport()
        settings = _simulation_settings(project_root)

        result = module.run_token_test(settings=settings, transport=transport)

        assert result.success is True
        assert result.expires_at is not None
        assert transport.token_call_count == 1
        assert KIS_VTS_REST_BASE_URL in transport.calls[0][0]

        module.print_result(result)
        output = capsys.readouterr().out
        assert "Status: SUCCESS" in output
        assert "Expires at:" in output
        assert "mock-access-token" not in output
        assert "test-app-secret" not in output

    def test_run_token_test_missing_credentials(self, project_root) -> None:
        module = _load_module(project_root)
        config = make_kats_config().model_copy(update={"environment": ENV_SIMULATION})
        secrets = replace(make_kis_secrets(), app_key="", app_secret="")
        settings = AppSettings.create(project_root, config, secrets)

        result = module.run_token_test(settings=settings, transport=MockHttpTransport())

        assert result.success is False
        assert "KIS_APP_KEY" in (result.error_message or "")

    def test_print_result_masks_error_secrets(self, project_root, capsys) -> None:
        module = _load_module(project_root)
        result = module.TokenTestResult(
            success=False,
            error_message="access_token=super-secret-token-value",
        )

        module.print_result(result)
        output = capsys.readouterr().out

        assert "Status: FAILED" in output
        assert "super-secret-token-value" not in output
        assert "access_token=" in output

    def test_main_returns_nonzero_without_credentials(
        self,
        project_root,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        module = _load_module(project_root)
        config = make_kats_config().model_copy(update={"environment": ENV_SIMULATION})
        secrets = replace(make_kis_secrets(), app_key="", app_secret="")
        settings = AppSettings.create(project_root, config, secrets)
        sources = module.SecretSources(
            app_key="missing",
            app_secret="missing",
            account_no="missing",
        )
        monkeypatch.setattr(module, "load_simulation_context", lambda _root: (settings, sources))

        assert module.main() == 1

    def test_main_success(self, project_root, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
        module = _load_module(project_root)
        expires = datetime.now(UTC) + timedelta(hours=12)
        settings = _simulation_settings(project_root)
        sources = module.SecretSources(app_key="env", app_secret="env", account_no="missing")
        monkeypatch.setattr(
            module,
            "load_simulation_context",
            lambda _root: (settings, sources),
        )
        monkeypatch.setattr(
            module,
            "run_token_test",
            lambda *, settings, transport=None: module.TokenTestResult(
                success=True,
                expires_at=expires,
            ),
        )

        assert module.main() == 0
        output = capsys.readouterr().out
        assert "APP_KEY source: env" in output
        assert "Status: SUCCESS" in output
        assert "Expires at:" in output
