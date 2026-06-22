"""Tests for scripts/test_current_price.py."""

from __future__ import annotations

import importlib.util
from dataclasses import replace

import pytest
from tests.fixtures.auth_fixtures import make_kats_config, make_kis_secrets
from tests.fixtures.market_fixtures import MockRestClient, sample_price_output

from app.broker.kis.api import ApiRegistry
from app.broker.kis.api.market_api_keys import INQUIRE_PRICE
from app.config.app_settings import AppSettings
from app.core.constants import ENV_SIMULATION

pytestmark = pytest.mark.unit


def _load_module(project_root):
    import sys

    script_path = project_root / "scripts" / "test_current_price.py"
    module_name = "test_current_price_script"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _simulation_settings(project_root) -> AppSettings:
    config = make_kats_config().model_copy(update={"environment": ENV_SIMULATION})
    return AppSettings.create(project_root, config, make_kis_secrets())


class TestCurrentPriceScript:
    """Tests for the KIS current price test script."""

    def test_project_root(self, project_root) -> None:
        module = _load_module(project_root)
        assert module.project_root() == project_root

    def test_run_current_price_test_success(self, project_root) -> None:
        module = _load_module(project_root)
        rest_client = MockRestClient(output=sample_price_output())
        settings = _simulation_settings(project_root)

        result = module.run_current_price_test(
            settings=settings,
            symbol_code="005930",
            rest_client=rest_client,
        )

        assert result.rt_cd == "0"
        assert result.msg_cd == "MCA00000"
        assert result.current_price == "70000"
        assert len(rest_client.calls) == 1
        call = rest_client.calls[0]
        assert call["path"] == "/uapi/domestic-stock/v1/quotations/inquire-price"
        assert call["params"]["FID_INPUT_ISCD"] == "005930"
        assert call["tr_id"] == "FHKST01010100"

    def test_run_current_price_test_uses_registry_tr_id(self, project_root) -> None:
        module = _load_module(project_root)
        from app.broker.kis.api.enums import ApiCategory, HttpMethod
        from app.broker.kis.api.metadata import ApiMetadata

        custom = ApiMetadata(
            api_key=INQUIRE_PRICE,
            name="Custom Price",
            category=ApiCategory.DOMESTIC_STOCK,
            method=HttpMethod.GET,
            path="/uapi/domestic-stock/v1/quotations/inquire-price",
            tr_id="FHKST99999",
            description="custom",
            sub_category="quotations",
            enabled=True,
        )
        registry = ApiRegistry.from_entries((custom,))
        rest_client = MockRestClient(output=sample_price_output())
        settings = _simulation_settings(project_root)

        module.run_current_price_test(
            settings=settings,
            registry=registry,
            rest_client=rest_client,
        )

        assert rest_client.calls[0]["tr_id"] == "FHKST99999"

    def test_print_result_outputs_required_fields_only(self, project_root, capsys) -> None:
        module = _load_module(project_root)
        result = module.CurrentPriceTestResult(
            rt_cd="0",
            msg_cd="MCA00000",
            msg1="ok",
            current_price="70000",
        )

        module.print_result(result)
        output = capsys.readouterr().out

        assert output == ("rt_cd: 0\n" "msg_cd: MCA00000\n" "msg1: ok\n" "current_price: 70000\n")
        assert "Bearer" not in output
        assert "access_token" not in output

    def test_run_current_price_test_missing_credentials(self, project_root) -> None:
        module = _load_module(project_root)
        config = make_kats_config().model_copy(update={"environment": ENV_SIMULATION})
        secrets = replace(make_kis_secrets(), app_key="", app_secret="")
        settings = AppSettings.create(project_root, config, secrets)

        result = module.run_current_price_test(settings=settings, rest_client=MockRestClient())

        assert result.rt_cd == "1"
        assert "KIS_APP_KEY" in result.msg1

    def test_main_success(self, project_root, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
        module = _load_module(project_root)
        settings = _simulation_settings(project_root)
        monkeypatch.setattr(module, "load_simulation_settings", lambda _root: settings)
        monkeypatch.setattr(
            module,
            "run_current_price_test",
            lambda **kwargs: module.CurrentPriceTestResult(
                rt_cd="0",
                msg_cd="MCA00000",
                msg1="ok",
                current_price="70000",
            ),
        )

        assert module.main() == 0
        output = capsys.readouterr().out
        assert "rt_cd: 0" in output
        assert "current_price: 70000" in output

    def test_samsung_symbol_constant(self, project_root) -> None:
        module = _load_module(project_root)
        assert module.SAMSUNG_SYMBOL == "005930"
