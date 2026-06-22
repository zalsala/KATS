"""Tests for scripts/test_orderable_amount.py."""

from __future__ import annotations

import importlib.util
from dataclasses import replace

import pytest
from tests.fixtures.account_fixtures import MockAccountRestClient, sample_psbl_order_response
from tests.fixtures.auth_fixtures import make_kats_config, make_kis_secrets

from app.broker.kis.api import ApiRegistry
from app.broker.kis.api.account_api_keys import INQUIRE_PSBL_ORDER
from app.config.app_settings import AppSettings
from app.core.constants import ENV_SIMULATION

pytestmark = pytest.mark.unit

PSBL_PATH = "/uapi/domestic-stock/v1/trading/inquire-psbl-order"


def _load_module(project_root):
    import sys

    script_path = project_root / "scripts" / "test_orderable_amount.py"
    module_name = "test_orderable_amount_script"
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


class TestOrderableAmountScript:
    """Tests for the KIS orderable amount test script."""

    def test_project_root(self, project_root) -> None:
        module = _load_module(project_root)
        assert module.project_root() == project_root

    def test_run_orderable_amount_test_success(self, project_root) -> None:
        module = _load_module(project_root)
        rest_client = MockAccountRestClient(
            responses_by_path={PSBL_PATH: sample_psbl_order_response()}
        )
        settings = _simulation_settings(project_root)

        result = module.run_orderable_amount_test(
            settings=settings,
            symbol_code="005930",
            rest_client=rest_client,
        )

        assert result.rt_cd == "0"
        assert result.msg_cd == "MCA00000"
        assert result.orderable_amount == "1500000"
        assert len(rest_client.calls) == 1
        call = rest_client.calls[0]
        assert call["path"] == PSBL_PATH
        assert call["params"]["PDNO"] == "005930"
        assert call["params"]["ORD_DVSN"] == "00"
        assert call["params"]["ORD_UNPR"] == "70000"
        assert call["params"]["ORD_QTY"] == "1"
        assert call["params"]["CANO"] == "12345678"
        assert call["tr_id"] == "VTTC8908R"

    def test_run_orderable_amount_test_uses_registry_tr_id(self, project_root) -> None:
        module = _load_module(project_root)
        from app.broker.kis.api.enums import ApiCategory, HttpMethod
        from app.broker.kis.api.metadata import ApiMetadata

        custom = ApiMetadata(
            api_key=INQUIRE_PSBL_ORDER,
            name="Custom Psbl Order",
            category=ApiCategory.DOMESTIC_STOCK,
            method=HttpMethod.GET,
            path=PSBL_PATH,
            tr_id="FHKST88888",
            description="custom",
            sub_category="trading",
            enabled=True,
        )
        registry = ApiRegistry.from_entries((custom,))
        rest_client = MockAccountRestClient(
            responses_by_path={PSBL_PATH: sample_psbl_order_response()}
        )
        settings = _simulation_settings(project_root)

        module.run_orderable_amount_test(
            settings=settings,
            registry=registry,
            rest_client=rest_client,
        )

        assert rest_client.calls[0]["tr_id"] == "FHKST88888"

    def test_print_result_outputs_required_fields_only(self, project_root, capsys) -> None:
        module = _load_module(project_root)
        result = module.OrderableAmountTestResult(
            rt_cd="0",
            msg_cd="MCA00000",
            msg1="ok",
            orderable_amount="1500000",
        )

        module.print_result(result)
        output = capsys.readouterr().out

        assert output == (
            "rt_cd: 0\n" "msg_cd: MCA00000\n" "msg1: ok\n" "orderable_amount: 1500000\n"
        )
        assert "12345678" not in output
        assert "Bearer" not in output

    def test_run_orderable_amount_test_missing_account_no(self, project_root) -> None:
        module = _load_module(project_root)
        config = make_kats_config().model_copy(update={"environment": ENV_SIMULATION})
        secrets = replace(make_kis_secrets(), account_no="")
        settings = AppSettings.create(project_root, config, secrets)

        result = module.run_orderable_amount_test(
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
            "run_orderable_amount_test",
            lambda **kwargs: module.OrderableAmountTestResult(
                rt_cd="0",
                msg_cd="MCA00000",
                msg1="ok",
                orderable_amount="1500000",
            ),
        )

        assert module.main() == 0
        output = capsys.readouterr().out
        assert "orderable_amount: 1500000" in output
        assert "rt_cd: 0" in output

    def test_orderable_amount_request_constants(self, project_root) -> None:
        module = _load_module(project_root)
        assert module.SAMSUNG_SYMBOL == "005930"
        assert module.ORDER_DIVISION_LIMIT == "00"
        assert module.TEST_ORDER_UNIT_PRICE == "70000"
        assert module.BUY_ORDER_QUANTITY == "1"
