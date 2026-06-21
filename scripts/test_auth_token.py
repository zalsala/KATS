"""KIS Access Token issuance test for simulation (VTS) environment."""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


def _bootstrap_import_path() -> None:
    """Allow ``python scripts/test_auth_token.py`` from the project root."""
    root = Path(__file__).resolve().parents[1]
    scripts_dir = Path(__file__).resolve().parent
    for path_str in (str(root), str(scripts_dir)):
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


_bootstrap_import_path()

import vts_common  # noqa: E402

from app.broker.kis.auth.auth_models import KIS_TIMEZONE  # noqa: E402
from app.broker.kis.auth.http_transport import HttpTransport  # noqa: E402
from app.config.app_settings import AppSettings  # noqa: E402

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class TokenTestResult:
    """Result of a KIS access token issuance test."""

    success: bool
    expires_at: datetime | None = None
    error_message: str | None = None


project_root = vts_common.project_root
load_simulation_context = vts_common.load_simulation_context
print_credential_diagnostics = vts_common.print_credential_diagnostics
SecretSources = vts_common.SecretSources


def run_token_test(
    *,
    settings: AppSettings,
    transport: HttpTransport | None = None,
) -> TokenTestResult:
    """Issue an access token without invoking order APIs."""
    error = vts_common.validate_simulation_environment(settings)
    if error is not None:
        return TokenTestResult(success=False, error_message=error)

    try:
        auth = vts_common.build_auth_components(settings, transport=transport)
        token = auth.token_manager.issue()
        return TokenTestResult(success=True, expires_at=token.expires_at)
    except Exception as exc:  # noqa: BLE001 - surface masked error to CLI
        return TokenTestResult(success=False, error_message=vts_common.mask_text(str(exc)))


def format_expiry(expires_at: datetime) -> str:
    """Format token expiry for CLI output."""
    return expires_at.astimezone(KIS_TIMEZONE).strftime("%Y-%m-%d %H:%M:%S %Z")


def print_result(result: TokenTestResult) -> None:
    """Print success status and expiry only (no token values)."""
    if result.success and result.expires_at is not None:
        print("Status: SUCCESS")
        print(f"Expires at: {format_expiry(result.expires_at)}")
        return

    print("Status: FAILED")
    if result.error_message:
        vts_common.print_masked("Error", result.error_message)


def main() -> int:
    """Run the KIS access token issuance test."""
    logging.basicConfig(level=logging.WARNING)
    root = project_root()
    settings, sources = load_simulation_context(root)
    print_credential_diagnostics(settings, sources)
    result = run_token_test(settings=settings)
    print_result(result)
    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
