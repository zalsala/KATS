"""Shared helpers for KATS VTS simulation test scripts."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.broker.kis.auth import AuthenticationComponents
    from app.broker.kis.auth.http_transport import HttpTransport
    from app.broker.kis.rest.http_transport import RestHttpTransport
    from app.broker.kis.rest.kis_rest_client import KisRestClient
    from app.config.app_settings import AppSettings
    from app.config.secret_manager import SecretSources
    from app.domain.account.value_objects.account_context import AccountContext

DEFAULT_ACCOUNT_PRODUCT = "01"


def bootstrap_import_path() -> Path:
    """Add project root and ``scripts/`` to ``sys.path`` for direct script execution."""
    root = Path(__file__).resolve().parents[1]
    scripts_dir = Path(__file__).resolve().parent
    for path in (root, scripts_dir):
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)
    return root


bootstrap_import_path()

from app.broker.kis.auth import (  # noqa: E402
    AuthenticationComponents,
    build_authentication_components,
)
from app.broker.kis.auth.http_transport import HttpTransport  # noqa: E402
from app.broker.kis.rest.http_transport import RestHttpTransport  # noqa: E402
from app.broker.kis.rest.kis_rest_client import KisRestClient, build_kis_rest_client  # noqa: E402
from app.config.app_settings import AppSettings  # noqa: E402
from app.config.config_manager import ConfigManager  # noqa: E402
from app.config.env_loader import EnvironmentLoader  # noqa: E402
from app.config.secret_manager import SecretSources  # noqa: E402
from app.core.constants import (  # noqa: E402
    DOTENV_FILE_NAME,
    ENV_KIS_ACCOUNT_PRODUCT,
    ENV_SIMULATION,
    KIS_VTS_REST_BASE_URL,
)
from app.core.logging.masker import SensitiveDataMasker  # noqa: E402
from app.domain.account.value_objects.account_context import AccountContext  # noqa: E402

_MASKER = SensitiveDataMasker()


def project_root() -> Path:
    """Return the KATS project root directory."""
    return Path(__file__).resolve().parents[1]


def load_simulation_settings(root: Path | None = None) -> AppSettings:
    """Load application settings forced to the simulation environment."""
    root = root or project_root()
    ConfigManager.reset_instance()
    manager = ConfigManager.get_instance(project_root=root, environment=ENV_SIMULATION)
    return manager.load()


def load_simulation_context(root: Path | None = None) -> tuple[AppSettings, SecretSources]:
    """Load simulation settings and credential source diagnostics."""
    root = root or project_root()
    env_result = EnvironmentLoader().load(
        root / DOTENV_FILE_NAME,
        ENV_SIMULATION,
    )
    settings = load_simulation_settings(root)
    return settings, env_result.secret_sources()


def build_auth_components(
    settings: AppSettings,
    *,
    transport: HttpTransport | RestHttpTransport | None = None,
) -> AuthenticationComponents:
    """Build KIS authentication components for VTS test scripts."""
    return build_authentication_components(settings, transport=transport)


def build_rest_client(
    settings: AppSettings,
    *,
    transport: RestHttpTransport | None = None,
) -> KisRestClient:
    """Wire ``KisRestClient`` for simulation REST API calls."""
    auth = build_authentication_components(settings, transport=transport)
    return build_kis_rest_client(
        broker_config=settings.config.broker,
        token_manager=auth.token_manager,
        header_builder=auth.header_builder,
        transport=transport,
        is_vts=settings.is_mock_account,
    )


def build_account_context(
    settings: AppSettings,
    *,
    account_product: str | None = None,
) -> AccountContext:
    """Build account context from environment-backed secrets."""
    product = account_product or os.getenv(ENV_KIS_ACCOUNT_PRODUCT, DEFAULT_ACCOUNT_PRODUCT)
    return AccountContext(
        account_no=settings.secrets.account_no,
        account_product=product,
    )


def mask_text(value: str) -> str:
    """Mask sensitive values for safe CLI output."""
    return _MASKER.mask(value)


def print_masked(label: str, value: str) -> None:
    """Print a single masked label/value pair."""
    print(f"{label}: {mask_text(value)}")


def validate_simulation_environment(
    settings: AppSettings,
    *,
    require_account: bool = False,
) -> str | None:
    """Return an error message when simulation prerequisites are not met."""
    if not settings.secrets.is_configured:
        return "KIS_APP_KEY and KIS_APP_SECRET are required in .env"
    if require_account and not settings.secrets.account_no:
        return "KIS_ACCOUNT_NO is required in .env"
    if settings.environment != ENV_SIMULATION:
        return f"Expected environment={ENV_SIMULATION}, got {settings.environment}"
    if KIS_VTS_REST_BASE_URL not in settings.kis_rest_base_url:
        return "Broker base URL is not the KIS VTS simulation endpoint"
    return None


def format_base_url(base_url: str) -> str:
    """Format broker base URL without exposing full credentials context."""
    host = base_url.removeprefix("https://").removeprefix("http://")
    if host.startswith("openapivts"):
        return "openapivts..."
    if len(host) > 24:
        return f"{host[:24]}..."
    return host


def print_credential_diagnostics(
    settings: AppSettings,
    sources: SecretSources,
) -> None:
    """Print credential sources and runtime endpoint summary only."""
    for line in sources.as_lines():
        print(line)
    print(f"BASE_URL: {format_base_url(settings.kis_rest_base_url)}")
    print(f"ACCOUNT_TYPE: {settings.secrets.account_type}")
