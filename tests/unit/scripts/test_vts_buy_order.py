"""Tests for scripts/test_vts_buy_order.py."""

from __future__ import annotations

import importlib.util
from dataclasses import replace

import pytest
from tests.fixtures.auth_fixtures import make_kats_config, make_kis_secrets
from tests.fixtures.order_fixtures import build_test_order_service, sample_order_cash_response

from app.config.app_settings import AppSettings
from app.core.constants import ENV_SIMULATION, KIS_ACCOUNT_MOCK, KIS_ACCOUNT_REAL

pytestmark = pytest.mark.unit

ORDER_CASH_PATH = "/uapi/domestic-stock/v1/trading/order-cash"


def _load_module(project_root):
    import sys

    script_path = project_root / "scripts" / "test_vts_buy_order.py"
    module_name = "test_vts_buy_order_script"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _simulation_settings(project_root) -> AppSettings:
    config = make_kats_config().model_copy(update={"environment": ENV_SIMULATION})
    secrets = replace(make_kis_secrets(), account_no="12345678", account_type=KIS_ACCOUNT_MOCK)
    return AppSettings.create(project_root, config, secrets)


class TestVtsBuyOrderScript:
    """Tests for the VTS mock buy order script."""

    def test_project_root(self, project_root) -> None:
        module = _load_module(project_root)
        assert module.project_root() == project_root

    def test_calculate_limit_buy_price(self, project_root) -> None:
        module = _load_module(project_root)
        assert module.calculate_limit_buy_price("70000") == "69900"
        assert module.calculate_limit_buy_price("50", offset=100) == "1"

    def test_validate_vts_buy_prerequisites_rejects_live_trading(self, project_root) -> None:
        module = _load_module(project_root)
        config = make_kats_config().model_copy(
            update={
                "environment": ENV_SIMULATION,
                "order": make_kats_config().order.model_copy(update={"live_trading_enabled": True}),
            }
        )
        secrets = replace(make_kis_secrets(), account_no="12345678")
        settings = AppSettings.create(project_root, config, secrets)

        error = module.validate_vts_buy_prerequisites(settings)

        assert error is not None
        assert "live_trading_enabled" in error

    def test_validate_vts_buy_prerequisites_rejects_real_account(self, project_root) -> None:
        module = _load_module(project_root)
        config = make_kats_config().model_copy(update={"environment": ENV_SIMULATION})
        secrets = replace(
            make_kis_secrets(),
            account_no="12345678",
            account_type=KIS_ACCOUNT_REAL,
        )
        settings = AppSettings.create(project_root, config, secrets)

        error = module.validate_vts_buy_prerequisites(settings)

        assert error is not None
        assert "mock" in error

    def test_run_vts_buy_order_requires_confirmation(self, project_root) -> None:
        module = _load_module(project_root)
        settings = _simulation_settings(project_root)

        result = module.run_vts_buy_order_test(
            settings=settings,
            user_confirmed=False,
            current_price="70000",
        )

        assert result.msg_cd == "CANCELLED"
        assert result.order_number == ""

    def test_run_vts_buy_order_places_limit_buy(self, project_root) -> None:
        module = _load_module(project_root)
        service, client, hashkey_manager = build_test_order_service(
            post_responses_by_path={ORDER_CASH_PATH: sample_order_cash_response()}
        )
        settings = _simulation_settings(project_root)

        result = module.run_vts_buy_order_test(
            settings=settings,
            user_confirmed=True,
            current_price="70000",
            order_service=service,
        )

        assert result.rt_cd == "0"
        assert result.order_number == "0000123456"
        assert len(client.calls) == 1
        body = client.calls[0]["body"]
        assert body["PDNO"] == "005930"
        assert body["ORD_QTY"] == "1"
        assert body["ORD_DVSN"] == "00"
        assert body["ORD_UNPR"] == "69900"
        assert body["SLL_BUY_DVSN_CD"] == "02"
        assert len(hashkey_manager.calls) == 1

    def test_print_result_outputs_required_fields_only(self, project_root, capsys) -> None:
        module = _load_module(project_root)
        result = module.VtsBuyOrderTestResult(
            rt_cd="0",
            msg_cd="MCA00000",
            msg1="ok",
            order_number="0000123456",
        )

        module.print_result(result)
        output = capsys.readouterr().out

        assert output == (
            "rt_cd: 0\n"
            "msg_cd: MCA00000\n"
            "msg1: ok\n"
            "order_number: 0000123456\n"
        )
        assert "12345678" not in output

    def test_prompt_user_confirmation(self, project_root) -> None:
        module = _load_module(project_root)
        assert module.prompt_user_confirmation(input_func=lambda: "YES") is True
        assert module.prompt_user_confirmation(input_func=lambda: "NO") is False

    def test_main_cancelled_exit_code(self, project_root, monkeypatch: pytest.MonkeyPatch) -> None:
        module = _load_module(project_root)
        settings = _simulation_settings(project_root)
        monkeypatch.setattr(module, "load_simulation_settings", lambda _root: settings)
        monkeypatch.setattr(
            module,
            "run_vts_buy_order_test",
            lambda **kwargs: module.VtsBuyOrderTestResult(
                rt_cd="1",
                msg_cd="CANCELLED",
                msg1="User did not confirm with YES",
                order_number="",
            ),
        )

        assert module.main() == 2
