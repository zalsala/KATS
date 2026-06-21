"""Application-wide constants for KATS."""

from __future__ import annotations

from typing import Final

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
APP_NAME: Final[str] = "KATS"
APP_VERSION: Final[str] = "1.0.0"
APP_TIMEZONE: Final[str] = "Asia/Seoul"

# ---------------------------------------------------------------------------
# Environment names
# ---------------------------------------------------------------------------
ENV_DEVELOPMENT: Final[str] = "development"
ENV_SIMULATION: Final[str] = "simulation"
ENV_PRODUCTION: Final[str] = "production"

SUPPORTED_ENVIRONMENTS: Final[frozenset[str]] = frozenset(
    {ENV_DEVELOPMENT, ENV_SIMULATION, ENV_PRODUCTION}
)

# ---------------------------------------------------------------------------
# Environment variable keys (KIS OpenAPI credentials)
# ---------------------------------------------------------------------------
ENV_KATS_ENV: Final[str] = "KATS_ENV"
ENV_KIS_APP_KEY: Final[str] = "KIS_APP_KEY"
ENV_KIS_APP_SECRET: Final[str] = "KIS_APP_SECRET"
ENV_KIS_ACCOUNT_NO: Final[str] = "KIS_ACCOUNT_NO"
ENV_KIS_ACCOUNT_TYPE: Final[str] = "KIS_ACCOUNT_TYPE"

SECRET_ENV_KEYS: Final[frozenset[str]] = frozenset(
    {
        ENV_KIS_APP_KEY,
        ENV_KIS_APP_SECRET,
        ENV_KIS_ACCOUNT_NO,
    }
)

# ---------------------------------------------------------------------------
# KIS OpenAPI REST endpoints (kis_devlp.yaml: prod / vps)
# ---------------------------------------------------------------------------
KIS_VTS_REST_BASE_URL: Final[str] = "https://openapivts.koreainvestment.com:29443"
KIS_REAL_REST_BASE_URL: Final[str] = "https://openapi.koreainvestment.com:9443"

# ---------------------------------------------------------------------------
# KIS OpenAPI WebSocket endpoints (kis_devlp.yaml: ops / vops)
# ---------------------------------------------------------------------------
KIS_VTS_WS_URL: Final[str] = "ws://ops.koreainvestment.com:31000"
KIS_REAL_WS_URL: Final[str] = "ws://ops.koreainvestment.com:21000"

# ---------------------------------------------------------------------------
# KIS server mode keys (kis_auth.py: svr parameter)
# ---------------------------------------------------------------------------
KIS_SVR_PROD: Final[str] = "prod"
KIS_SVR_VPS: Final[str] = "vps"

# ---------------------------------------------------------------------------
# KIS OAuth / HashKey paths (official API)
# ---------------------------------------------------------------------------
KIS_OAUTH_TOKEN_PATH: Final[str] = "/oauth2/tokenP"
KIS_OAUTH_APPROVAL_PATH: Final[str] = "/oauth2/Approval"
KIS_HASHKEY_PATH: Final[str] = "/uapi/hashkey"

# ---------------------------------------------------------------------------
# KIS account product codes (kis_devlp.yaml: my_prod)
# ---------------------------------------------------------------------------
KIS_PRODUCT_STOCK: Final[str] = "01"
KIS_PRODUCT_FUTURE: Final[str] = "03"
KIS_PRODUCT_OVERSEAS_FUTURE: Final[str] = "08"
KIS_PRODUCT_PENSION: Final[str] = "22"
KIS_PRODUCT_RETIREMENT: Final[str] = "29"
KIS_DEFAULT_PRODUCT: Final[str] = KIS_PRODUCT_STOCK

# ---------------------------------------------------------------------------
# KIS rate limiting (kis_auth.py: smart_sleep)
# ---------------------------------------------------------------------------
KIS_RATE_LIMIT_SLEEP_PROD: Final[float] = 0.05
KIS_RATE_LIMIT_SLEEP_VPS: Final[float] = 0.5
KIS_TOKEN_VALIDITY_SECONDS: Final[int] = 86400

# ---------------------------------------------------------------------------
# KIS environment variable keys (extended)
# ---------------------------------------------------------------------------
ENV_KIS_HTS_ID: Final[str] = "KIS_HTS_ID"
ENV_KIS_ACCOUNT_PRODUCT: Final[str] = "KIS_ACCOUNT_PRODUCT"
ENV_KIS_PAPER_ACCOUNT_NO: Final[str] = "KIS_PAPER_ACCOUNT_NO"

# ---------------------------------------------------------------------------
# KIS account types
# ---------------------------------------------------------------------------
KIS_ACCOUNT_MOCK: Final[str] = "mock"
KIS_ACCOUNT_REAL: Final[str] = "real"

# ---------------------------------------------------------------------------
# HTTP defaults (KIS OpenAPI)
# ---------------------------------------------------------------------------
DEFAULT_CONNECT_TIMEOUT: Final[int] = 5
DEFAULT_READ_TIMEOUT: Final[int] = 10
DEFAULT_WRITE_TIMEOUT: Final[int] = 10
DEFAULT_MAX_RETRY: Final[int] = 3
DEFAULT_BACKOFF_FACTOR: Final[int] = 2
DEFAULT_REST_TIMEOUT: Final[int] = 10
DEFAULT_WS_TIMEOUT: Final[int] = 30

# ---------------------------------------------------------------------------
# Rate limiting (KIS OpenAPI)
# ---------------------------------------------------------------------------
DEFAULT_REQUESTS_PER_SECOND: Final[int] = 20
DEFAULT_BURST_SIZE: Final[int] = 5

# ---------------------------------------------------------------------------
# Configuration file names
# ---------------------------------------------------------------------------
CONFIG_DEFAULT_FILE: Final[str] = "default.json"
CONFIG_DIR_NAME: Final[str] = "config"
DATA_DIR_NAME: Final[str] = "data"
SETTINGS_FILE_NAME: Final[str] = "settings.json"
DOTENV_FILE_NAME: Final[str] = ".env"

# ---------------------------------------------------------------------------
# Hot-reloadable configuration sections
# ---------------------------------------------------------------------------
HOT_RELOAD_SECTIONS: Final[frozenset[str]] = frozenset(
    {"logging", "notification", "ui", "strategy", "market"}
)

# ---------------------------------------------------------------------------
# Sensitive configuration paths (never persisted to settings.json)
# ---------------------------------------------------------------------------
SECRET_CONFIG_PATHS: Final[frozenset[tuple[str, ...]]] = frozenset(
    {
        ("authentication", "app_key"),
        ("authentication", "app_secret"),
        ("authentication", "account_no"),
    }
)

# Masking
SECRET_MASK: Final[str] = "****"
