"""Pydantic configuration models for KATS."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class RetryConfig(BaseModel):
    """HTTP retry configuration."""

    max_retry: int = Field(default=3, ge=0, le=10)
    backoff_factor: int = Field(default=2, ge=1, le=10)


class TimeoutConfig(BaseModel):
    """HTTP timeout configuration in seconds."""

    connect: int = Field(default=5, ge=1, le=60)
    read: int = Field(default=10, ge=1, le=120)
    write: int = Field(default=10, ge=1, le=120)


class RateLimitConfig(BaseModel):
    """API rate limit configuration."""

    requests_per_second: int = Field(default=20, ge=1, le=100)
    burst_size: int = Field(default=5, ge=1, le=50)


class ApplicationConfig(BaseModel):
    """Application-level settings."""

    name: str = "KATS"
    version: str = "1.0.0"
    language: str = "ko"
    theme: Literal["light", "dark"] = "dark"
    debug: bool = False
    timezone: str = "Asia/Seoul"


class BrokerConfig(BaseModel):
    """Broker connection settings."""

    broker_type: str = "kis"
    base_url: str
    websocket_url: str
    timeout: TimeoutConfig = Field(default_factory=TimeoutConfig)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)

    @field_validator("base_url", "websocket_url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        """Validate that broker URLs use http(s) or ws(s) scheme."""
        if not value.startswith(("http://", "https://", "ws://", "wss://")):
            msg = f"Invalid URL scheme: {value}"
            raise ValueError(msg)
        return value


class AuthenticationConfig(BaseModel):
    """Authentication settings. Sensitive values come from environment only."""

    app_key: str = ""
    app_secret: str = ""
    account_no: str = ""
    account_type: Literal["mock", "real"] = "mock"
    token_path: str = "data/auth/token.json"
    auto_refresh: bool = True
    refresh_margin_seconds: int = Field(default=300, ge=60, le=3600)
    approval_cache_seconds: int = Field(default=3600, ge=60, le=86400)


class DatabaseConfig(BaseModel):
    """Database settings."""

    engine: Literal["sqlite", "postgresql"] = "sqlite"
    database_path: str = "data/database/kats.db"
    backup_path: str = "data/backup"
    migration_enabled: bool = True
    cache_enabled: bool = True
    pool_size: int = Field(default=5, ge=1, le=50)


class LoggingConfig(BaseModel):
    """Logging settings."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    structured: bool = False
    rotation: bool = True
    max_file_size_mb: int = Field(default=10, ge=1, le=100)
    backup_count: int = Field(default=5, ge=1, le=30)
    console_output: bool = True
    file_output: bool = True


class StrategyConfig(BaseModel):
    """Strategy engine settings."""

    auto_load: bool = True
    plugin_path: str = "plugins/strategies"
    scan_interval_seconds: int = Field(default=60, ge=10, le=3600)
    max_strategy_count: int = Field(default=10, ge=1, le=100)
    auto_start: bool = False


class BacktestConfig(BaseModel):
    """Backtest engine settings."""

    default_slippage: float = Field(default=0.001, ge=0.0, le=0.1)
    default_commission_rate: float = Field(default=0.00015, ge=0.0, le=0.01)
    default_initial_capital: int = Field(default=10_000_000, ge=1)


class MarketConfig(BaseModel):
    """Market data settings."""

    cache_ttl_seconds: int = Field(default=1, ge=0, le=60)
    tick_buffer_size: int = Field(default=1000, ge=100, le=100_000)
    candle_buffer_size: int = Field(default=500, ge=50, le=10_000)
    refresh_interval_seconds: int = Field(default=1, ge=1, le=60)
    timezone: str = "Asia/Seoul"


class OrderConfig(BaseModel):
    """Order execution settings."""

    default_order_type: Literal["limit", "market"] = "limit"
    live_trading_enabled: bool = False
    retry: RetryConfig = Field(default_factory=RetryConfig)
    timeout_seconds: int = Field(default=10, ge=1, le=120)
    partial_fill_enabled: bool = True
    auto_cancel_seconds: int = Field(default=0, ge=0, le=3600)


class RiskConfig(BaseModel):
    """Risk management settings."""

    daily_loss_limit: float = Field(default=0.03, ge=0.0, le=1.0)
    position_limit: int = Field(default=20, ge=1, le=200)
    max_quantity: int = Field(default=10_000, ge=1)
    max_order_amount: int = Field(default=100_000_000, ge=1)
    duplicate_order_block: bool = True
    emergency_stop: bool = False


class NotificationConfig(BaseModel):
    """Notification settings."""

    enable_telegram: bool = False
    enable_discord: bool = False
    enable_email: bool = False
    enable_slack: bool = False
    sound_enabled: bool = True


class UiConfig(BaseModel):
    """UI settings."""

    theme: Literal["light", "dark"] = "dark"
    font: str = "Malgun Gothic"
    window_width: int = Field(default=1920, ge=800, le=7680)
    window_height: int = Field(default=1080, ge=600, le=4320)
    layout: str = "default"
    chart_style: str = "candle"
    language: str = "ko"


class SystemConfig(BaseModel):
    """System-level settings."""

    auto_backup: bool = True
    health_check_interval_seconds: int = Field(default=30, ge=5, le=300)
    recovery_timeout_seconds: int = Field(default=30, ge=5, le=300)


class SchedulerConfig(BaseModel):
    """Scheduler settings."""

    enabled: bool = False
    strategy_auto_start: bool = False
    strategy_auto_start_id: str = ""
    log_cleanup_interval_seconds: int = Field(default=86400, ge=60, le=604_800)


class KatsConfig(BaseModel):
    """Root configuration model for KATS."""

    application: ApplicationConfig = Field(default_factory=ApplicationConfig)
    broker: BrokerConfig
    authentication: AuthenticationConfig = Field(default_factory=AuthenticationConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    strategy: StrategyConfig = Field(default_factory=StrategyConfig)
    backtest: BacktestConfig = Field(default_factory=BacktestConfig)
    market: MarketConfig = Field(default_factory=MarketConfig)
    order: OrderConfig = Field(default_factory=OrderConfig)
    risk: RiskConfig = Field(default_factory=RiskConfig)
    notification: NotificationConfig = Field(default_factory=NotificationConfig)
    ui: UiConfig = Field(default_factory=UiConfig)
    system: SystemConfig = Field(default_factory=SystemConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    environment: Literal["development", "simulation", "production"] = "development"

    def resolve_path(self, relative_path: str) -> Path:
        """Resolve a configuration path relative to the project root."""
        path = Path(relative_path)
        if path.is_absolute():
            return path
        return path
