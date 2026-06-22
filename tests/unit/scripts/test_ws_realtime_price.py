"""Tests for scripts/test_ws_realtime_price.py."""

from __future__ import annotations

import importlib.util
import json
from dataclasses import replace
from unittest.mock import MagicMock

import pytest
from tests.fixtures.auth_fixtures import MockHttpTransport, make_kats_config, make_kis_secrets
from tests.fixtures.ws_fixtures import (
    MockWsTransport,
    build_test_websocket_service,
    sample_price_pipe_message,
)

from app.broker.kis.websocket.ws_tr_ids import WS_TR_REALTIME_PRICE
from app.config.app_settings import AppSettings
from app.core.constants import ENV_SIMULATION, KIS_ACCOUNT_REAL

pytestmark = pytest.mark.unit


def _load_module(project_root):
    import sys

    script_path = project_root / "scripts" / "test_ws_realtime_price.py"
    module_name = "test_ws_realtime_price_script"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _simulation_settings(project_root) -> AppSettings:
    config = make_kats_config().model_copy(update={"environment": ENV_SIMULATION})
    return AppSettings.create(project_root, config, make_kis_secrets())


class TestWsRealtimePriceScript:
    """Tests for the VTS WebSocket realtime price script."""

    def test_project_root(self, project_root) -> None:
        module = _load_module(project_root)
        assert module.project_root() == project_root

    def test_validate_ws_prerequisites_rejects_real_account(self, project_root) -> None:
        module = _load_module(project_root)
        config = make_kats_config().model_copy(update={"environment": ENV_SIMULATION})
        secrets = replace(make_kis_secrets(), account_type=KIS_ACCOUNT_REAL)
        settings = AppSettings.create(project_root, config, secrets)

        error = module.validate_ws_prerequisites(settings)

        assert error is not None
        assert "mock" in error

    def test_validate_ws_prerequisites_accepts_simulation_mock(self, project_root) -> None:
        module = _load_module(project_root)
        settings = _simulation_settings(project_root)

        assert module.validate_ws_prerequisites(settings) is None

    def test_build_price_subscribe_payload(self, project_root) -> None:
        module = _load_module(project_root)
        payload = module.build_price_subscribe_payload("approval-key-value", "005930")
        parsed = json.loads(payload)

        assert parsed["header"]["approval_key"] == "approval-key-value"
        assert parsed["header"]["tr_type"] == "1"
        assert parsed["body"]["input"]["tr_id"] == WS_TR_REALTIME_PRICE
        assert parsed["body"]["input"]["tr_key"] == "005930"

    def test_run_ws_realtime_price_issues_approval_key(self, project_root, tmp_path) -> None:
        module = _load_module(project_root)
        service, transport, _client = build_test_websocket_service(
            tmp_path,
            incoming_messages=[sample_price_pipe_message()],
        )
        settings = _simulation_settings(project_root)
        auth_transport = MockHttpTransport()
        auth = module.vts_common.build_auth_components(settings, transport=auth_transport)
        approval_manager = MagicMock(wraps=auth.approval_key_manager)
        auth = replace(auth, approval_key_manager=approval_manager)

        result = module.run_ws_realtime_price_test(
            settings=settings,
            websocket_service=service,
            auth=auth,
        )

        assert approval_manager.issue.called
        assert result.rt_cd == "0"
        assert transport.connect_calls
        assert transport.closed is True

    def test_run_ws_realtime_price_receive_success(self, project_root, tmp_path) -> None:
        module = _load_module(project_root)
        service, transport, _client = build_test_websocket_service(
            tmp_path,
            incoming_messages=[sample_price_pipe_message()],
        )
        settings = _simulation_settings(project_root)

        result = module.run_ws_realtime_price_test(
            settings=settings,
            websocket_service=service,
            auth_transport=MockHttpTransport(),
        )

        assert result.rt_cd == "0"
        assert result.status == "CONNECTED"
        assert result.subscribed == "005930"
        assert result.message_received is True
        assert "symbol=005930" in result.sample_message
        assert "price=70000" in result.sample_message
        assert len(transport.sent) == 1
        assert WS_TR_REALTIME_PRICE in transport.sent[0]

    def test_run_ws_realtime_price_timeout_failure(self, project_root, tmp_path) -> None:
        module = _load_module(project_root)
        service, transport, _client = build_test_websocket_service(tmp_path, incoming_messages=[])
        settings = _simulation_settings(project_root)

        result = module.run_ws_realtime_price_test(
            settings=settings,
            websocket_service=service,
            auth_transport=MockHttpTransport(),
            max_wait_seconds=0.2,
        )

        assert result.rt_cd == "1"
        assert result.status == "FAILED"
        assert "No realtime message" in result.msg1
        assert transport.closed is True

    def test_run_ws_realtime_price_connect_failure(self, project_root, tmp_path) -> None:
        module = _load_module(project_root)
        from app.broker.kis.websocket.kis_ws_client import KisWebSocketClient
        from app.broker.kis.websocket.reconnect_manager import ReconnectManager
        from app.broker.kis.websocket.subscription_manager import SubscriptionManager
        from app.service.websocket.websocket_service import WebSocketService

        transport = MockWsTransport(fail_connect=True)
        settings = _simulation_settings(project_root)
        auth = module.vts_common.build_auth_components(
            settings,
            transport=MockHttpTransport(),
        )
        ws_client = KisWebSocketClient(
            websocket_url=settings.kis_websocket_url,
            transport=transport,
            approval_key_manager=auth.approval_key_manager,
            header_builder=auth.header_builder,
            subscription_manager=SubscriptionManager(),
            reconnect_manager=ReconnectManager(),
        )
        service = WebSocketService(ws_client=ws_client)

        result = module.run_ws_realtime_price_test(
            settings=settings,
            websocket_service=service,
            auth=auth,
        )

        assert result.rt_cd == "1"
        assert result.status == "FAILED"
        assert "connection" in result.msg1.lower()

    def test_print_result_success(self, project_root, capsys) -> None:
        module = _load_module(project_root)
        result = module.WsRealtimePriceTestResult(
            rt_cd="0",
            status="CONNECTED",
            subscribed="005930",
            message_received=True,
            sample_message="symbol=005930 price=70000 trade_time=154208",
        )

        module.print_result(result)
        output = capsys.readouterr().out

        assert "rt_cd: 0" in output
        assert "status: CONNECTED" in output
        assert "subscribed: 005930" in output
        assert "message_received: true" in output
        assert "sample_message: symbol=005930" in output
        assert "approval" not in output.lower()

    def test_main_success(self, project_root, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
        module = _load_module(project_root)
        settings = _simulation_settings(project_root)
        monkeypatch.setattr(module, "load_simulation_settings", lambda _root: settings)
        monkeypatch.setattr(
            module,
            "run_ws_realtime_price_test",
            lambda **kwargs: module.WsRealtimePriceTestResult(
                rt_cd="0",
                status="CONNECTED",
                subscribed="005930",
                message_received=True,
                sample_message="symbol=005930 price=70000 trade_time=154208",
            ),
        )

        assert module.main() == 0
        output = capsys.readouterr().out
        assert "message_received: true" in output
