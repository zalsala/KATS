"""Tests for scripts/test_order_inquiry.py."""

from __future__ import annotations

import importlib.util
from dataclasses import replace

import pytest
from tests.fixtures.account_fixtures import MockAccountRestClient, sample_trade_history_response
from tests.fixtures.auth_fixtures import make_kats_config, make_kis_secrets

from app.broker.kis.api import ApiRegistry
from app.broker.kis.api.account_api_keys import INQUIRE_DAILY_CCLD
from app.config.app_settings import AppSettings
from app.core.constants import ENV_SIMULATION
from app.dto.account.trade_history_dto import TradeHistoryDto

pytestmark = pytest.mark.unit

CCLD_PATH = "/uapi/domestic-stock/v1/trading/inquire-daily-ccld"


def _load_module(project_root):
    import sys

    script_path = project_root / "scripts" / "test_order_inquiry.py"
    module_name = "test_order_inquiry_script"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _simulation_settings(project_root) -> AppSettings:
    config = make_kats_config().model_copy(update={"environment": ENV_SIMULATION})
    secrets = replace(make_kis_secrets(), account_no="12345678")
    return AppSettings.create(project_root, config, secrets)


class TestOrderInquiryScript:
    """Tests for the daily order inquiry script."""

    def test_project_root(self, project_root) -> None:
        module = _load_module(project_root)
        assert module.project_root() == project_root

    def test_run_order_inquiry_test_success(self, project_root) -> None:
        module = _load_module(project_root)
        rest_client = MockAccountRestClient(
            responses_by_path={CCLD_PATH: sample_trade_history_response()}
        )
        settings = _simulation_settings(project_root)

        result = module.run_order_inquiry_test(
            settings=settings,
            start_date="20260620",
            end_date="20260620",
            rest_client=rest_client,
        )

        assert result.rt_cd == "0"
        assert result.msg_cd == "MCA00000"
        assert result.order_count == 1
        assert result.orders[0].order_number == "00001234"
        assert result.orders[0].symbol == "005930"
        assert result.orders[0].quantity == "1"
        assert result.orders[0].status == "filled"
        call = rest_client.calls[0]
        assert call["path"] == CCLD_PATH
        assert call["tr_id"] == "VTTC0081R"
        assert call["params"]["CANO"] == "12345678"

    def test_run_order_inquiry_test_empty_history(self, project_root) -> None:
        module = _load_module(project_root)
        rest_client = MockAccountRestClient(responses_by_path={CCLD_PATH: {"output1": []}})
        settings = _simulation_settings(project_root)

        result = module.run_order_inquiry_test(
            settings=settings,
            start_date="20260620",
            end_date="20260620",
            rest_client=rest_client,
        )

        assert result.rt_cd == "0"
        assert result.order_count == 0
        assert result.orders == ()

    def test_run_order_inquiry_test_uses_registry_tr_id(self, project_root) -> None:
        module = _load_module(project_root)
        from app.broker.kis.api.enums import ApiCategory, HttpMethod
        from app.broker.kis.api.metadata import ApiMetadata

        custom = ApiMetadata(
            api_key=INQUIRE_DAILY_CCLD,
            name="Custom Daily Ccld",
            category=ApiCategory.DOMESTIC_STOCK,
            method=HttpMethod.GET,
            path=CCLD_PATH,
            tr_id="FHKST88888",
            description="custom",
            sub_category="trading",
            enabled=True,
        )
        registry = ApiRegistry.from_entries((custom,))
        rest_client = MockAccountRestClient(
            responses_by_path={CCLD_PATH: sample_trade_history_response()}
        )
        settings = _simulation_settings(project_root)

        module.run_order_inquiry_test(
            settings=settings,
            start_date="20260620",
            end_date="20260620",
            registry=registry,
            rest_client=rest_client,
        )

        assert rest_client.calls[0]["tr_id"] == "FHKST88888"

    def test_resolve_order_status(self, project_root) -> None:
        module = _load_module(project_root)
        filled = TradeHistoryDto(executed_quantity="1")
        pending = TradeHistoryDto(executed_quantity="0")

        assert module.resolve_order_status(filled) == "filled"
        assert module.resolve_order_status(pending) == "pending"

    def test_print_result_outputs_order_rows(self, project_root, capsys) -> None:
        module = _load_module(project_root)
        result = module.OrderInquiryTestResult(
            rt_cd="0",
            msg_cd="MCA00000",
            msg1="ok",
            order_count=1,
            orders=(
                module.OrderInquiryRow(
                    order_number="00001234",
                    symbol="005930",
                    quantity="1",
                    status="filled",
                ),
            ),
        )

        module.print_result(result)
        output = capsys.readouterr().out

        assert "order_count: 1" in output
        assert "order_number: 00001234" in output
        assert "symbol: 005930" in output
        assert "quantity: 1" in output
        assert "status: filled" in output
        assert "12345678" not in output

    def test_run_order_inquiry_test_missing_account_no(self, project_root) -> None:
        module = _load_module(project_root)
        config = make_kats_config().model_copy(update={"environment": ENV_SIMULATION})
        secrets = replace(make_kis_secrets(), account_no="")
        settings = AppSettings.create(project_root, config, secrets)

        result = module.run_order_inquiry_test(
            settings=settings,
            rest_client=MockAccountRestClient(),
        )

        assert result.rt_cd == "1"
        assert "KIS_ACCOUNT_NO" in result.msg1

    def test_main_success(self, project_root, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
        module = _load_module(project_root)
        settings = _simulation_settings(project_root)
        monkeypatch.setattr(module, "load_simulation_settings", lambda _root: settings)
        monkeypatch.setattr(
            module,
            "run_order_inquiry_test",
            lambda **kwargs: module.OrderInquiryTestResult(
                rt_cd="0",
                msg_cd="MCA00000",
                msg1="ok",
                order_count=0,
            ),
        )

        assert module.main() == 0
        output = capsys.readouterr().out
        assert "order_count: 0" in output
