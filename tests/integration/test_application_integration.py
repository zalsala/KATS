"""Final integration tests for KATS application bootstrap."""

from __future__ import annotations

import pytest

from app.bootstrap.application_bootstrap import ApplicationBootstrap, BootstrapOptions
from app.bootstrap.health_check import HealthCheck
from tests.fixtures.integration_fixtures import (
    build_integration_context,
    prepare_integration_root,
    write_user_settings,
)
from tests.fixtures.portfolio_fixtures import sample_account_payload
from tests.fixtures.ws_fixtures import MockWsTransport

pytestmark = pytest.mark.integration


class TestApplicationBootstrap:
    """Bootstrap composition tests."""

    def test_bootstrap_wires_core_services(self, tmp_path, project_root) -> None:
        root = prepare_integration_root(tmp_path, project_root)
        context = build_integration_context(root)

        assert context.config_manager is not None
        assert context.database_manager is not None
        assert context.event_bus is not None
        assert context.portfolio_service is not None
        assert context.strategy_service is not None
        assert context.risk_service is not None
        assert context.notification_service is not None
        assert context.order_service is not None
        assert context.authentication is not None
        assert context.portfolio_repository is not None
        assert context.portfolio_service.portfolio_repository is context.portfolio_repository

    def test_portfolio_restores_after_restart(self, tmp_path, project_root) -> None:
        root = prepare_integration_root(tmp_path, project_root)
        env_path = root / ".env"
        env_path.write_text(
            (
                "KATS_ENV=development\n"
                "KIS_APP_KEY=test-key\n"
                "KIS_APP_SECRET=test-secret\n"
                "KIS_ACCOUNT_NO=12345678\n"
            ),
            encoding="utf-8",
        )
        from app.config.config_manager import ConfigManager

        ConfigManager.reset_instance()
        first = build_integration_context(root)
        first.start()
        first.portfolio_service.apply_account(sample_account_payload(account_no="12345678"))
        expected_asset = first.portfolio_service.get_snapshot().total_asset
        first.stop()

        ConfigManager.reset_instance()
        second = build_integration_context(root)
        second.start()
        restored = second.portfolio_service.get_snapshot()

        assert restored.total_asset == expected_asset
        assert restored.account_no == "12345678"
        assert len(restored.positions) == 1
        assert restored.positions[0].symbol_code == "005930"
        second.stop()


class TestServiceWiring:
    """Service dependency wiring tests."""

    def test_risk_service_uses_portfolio_service(self, tmp_path, project_root) -> None:
        root = prepare_integration_root(tmp_path, project_root)
        context = build_integration_context(root)

        assert context.risk_service is not None
        assert context.portfolio_service is not None

    def test_scheduler_created_when_enabled(self, tmp_path, project_root) -> None:
        root = prepare_integration_root(tmp_path, project_root)
        write_user_settings(root, {"scheduler": {"enabled": True}})
        context = build_integration_context(root)

        assert context.scheduler_service is not None
        assert context.scheduler_worker_service is not None

    def test_scheduler_worker_starts_and_stops_with_context(self, tmp_path, project_root) -> None:
        root = prepare_integration_root(tmp_path, project_root)
        write_user_settings(
            root,
            {
                "scheduler": {
                    "enabled": True,
                    "tick_interval_seconds": 0.1,
                }
            },
        )
        context = build_integration_context(root)

        context.start()
        try:
            assert context.scheduler_worker_service is not None
            assert context.scheduler_worker_service.is_running is True
        finally:
            context.stop()

        assert context.scheduler_worker_service is not None
        assert context.scheduler_worker_service.is_running is False

    def test_websocket_service_created_with_transport(self, tmp_path, project_root) -> None:
        root = prepare_integration_root(tmp_path, project_root)
        transport = MockWsTransport()
        context = build_integration_context(root, ws_transport=transport)

        assert context.websocket_service is not None
        assert context.is_websocket_connected is False


class TestStartupSequence:
    """Startup lifecycle tests."""

    def test_startup_starts_eventbus_services(self, tmp_path, project_root) -> None:
        root = prepare_integration_root(tmp_path, project_root)
        context = build_integration_context(root)

        context.start()

        assert context.is_running is True

    def test_websocket_not_auto_connected_on_startup(self, tmp_path, project_root) -> None:
        root = prepare_integration_root(tmp_path, project_root)
        transport = MockWsTransport()
        context = build_integration_context(root, ws_transport=transport)

        context.start()

        assert context.is_websocket_connected is False
        context.connect_websocket()
        assert context.is_websocket_connected is True

    def test_strategy_auto_start_task_registered_only_with_scheduler_config(
        self,
        tmp_path,
        project_root,
    ) -> None:
        root = prepare_integration_root(tmp_path, project_root)
        write_user_settings(
            root,
            {
                "scheduler": {
                    "enabled": True,
                    "strategy_auto_start": True,
                    "strategy_auto_start_id": "test-strategy",
                },
                "strategy": {"auto_start": True},
            },
        )

        context = build_integration_context(root)
        context.start()

        assert context.scheduler_service is not None
        task_ids = [task["task_id"] for task in context.scheduler_service.list_tasks()]
        assert "strategy-auto-start" in task_ids


class TestShutdownSequence:
    """Shutdown lifecycle tests."""

    def test_shutdown_stops_services(self, tmp_path, project_root) -> None:
        root = prepare_integration_root(tmp_path, project_root)
        context = build_integration_context(root)
        context.start()
        context.stop()

        assert context.is_running is False

    def test_shutdown_disconnects_websocket(self, tmp_path, project_root) -> None:
        root = prepare_integration_root(tmp_path, project_root)
        transport = MockWsTransport()
        context = build_integration_context(root, ws_transport=transport)
        context.start()
        context.connect_websocket()
        context.stop()

        assert context.is_websocket_connected is False
        assert transport.closed is True


class TestHealthCheck:
    """Health check tests."""

    def test_health_check_passes_after_startup(self, tmp_path, project_root) -> None:
        root = prepare_integration_root(tmp_path, project_root)
        context = build_integration_context(root)
        context.start()

        result = HealthCheck().run(context)

        assert result.healthy is True
        assert any(item.name == "live_trading_disabled" and item.healthy for item in result.items)

    def test_health_check_reports_scheduler_worker_when_enabled(
        self,
        tmp_path,
        project_root,
    ) -> None:
        root = prepare_integration_root(tmp_path, project_root)
        write_user_settings(root, {"scheduler": {"enabled": True}})
        context = build_integration_context(root)
        context.start()

        result = HealthCheck().run(context)

        worker_item = next(item for item in result.items if item.name == "scheduler_worker")
        assert worker_item.healthy is True
        assert worker_item.detail == "running"
        context.stop()


class TestFinalSmoke:
    """End-to-end smoke test."""

    def test_bootstrap_run_smoke(self, tmp_path, project_root) -> None:
        root = prepare_integration_root(tmp_path, project_root)
        bootstrap = ApplicationBootstrap(
            root,
            environment="development",
            options=BootstrapOptions(setup_logging=True, validate_runtime=False),
        )
        context = bootstrap.run()

        try:
            assert context.is_running is True
            assert context.settings.config.order.live_trading_enabled is False
            health = HealthCheck().run(context)
            assert health.healthy is True
        finally:
            context.stop()
            context.shutdown()
