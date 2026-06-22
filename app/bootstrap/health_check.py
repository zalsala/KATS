"""Runtime health checks for KATS."""

from __future__ import annotations

from dataclasses import dataclass

from app.context.application_context import ApplicationContext


@dataclass(frozen=True, slots=True)
class HealthCheckItem:
    """Single health check result."""

    name: str
    healthy: bool
    detail: str


@dataclass(frozen=True, slots=True)
class HealthCheckResult:
    """Aggregated health check report."""

    healthy: bool
    items: tuple[HealthCheckItem, ...]

    def summary(self) -> str:
        """Return a human-readable summary."""
        status = "healthy" if self.healthy else "unhealthy"
        details = ", ".join(
            f"{item.name}={'ok' if item.healthy else 'fail'}" for item in self.items
        )
        return f"{status}: {details}"


class HealthCheck:
    """Validate that core runtime components are ready."""

    def run(self, context: ApplicationContext) -> HealthCheckResult:
        """Execute health checks against a running application context."""
        websocket_detail = (
            "connected"
            if context.is_websocket_connected
            else "not connected (explicit connect required)"
        )

        scheduler_enabled = context.settings.config.scheduler.enabled
        scheduler_ok = context.scheduler_service is not None if scheduler_enabled else True
        scheduler_detail = "enabled" if scheduler_enabled else "disabled"

        worker_ok, worker_detail = _scheduler_worker_health(context)

        plugins_ok, plugins_detail = _plugin_health(context)

        items = (
            HealthCheckItem("config", True, f"environment={context.settings.environment}"),
            HealthCheckItem(
                "database",
                context.database_manager.database_path.parent.exists(),
                f"path={context.database_manager.database_path}",
            ),
            HealthCheckItem("event_bus", context.event_bus is not None, "EventBusService ready"),
            HealthCheckItem(
                "services",
                context.is_running,
                "portfolio/strategy/risk/notification started",
            ),
            HealthCheckItem(
                "live_trading_disabled",
                not context.settings.config.order.live_trading_enabled,
                f"live_trading={context.settings.config.order.live_trading_enabled}",
            ),
            HealthCheckItem("websocket", True, websocket_detail),
            HealthCheckItem("scheduler", scheduler_ok, scheduler_detail),
            HealthCheckItem("scheduler_worker", worker_ok, worker_detail),
            HealthCheckItem("plugins", plugins_ok, plugins_detail),
        )
        healthy = all(item.healthy for item in items)
        return HealthCheckResult(healthy=healthy, items=items)


def _scheduler_worker_health(context: ApplicationContext) -> tuple[bool, str]:
    """Summarize scheduler worker status for health checks."""
    if not context.settings.config.scheduler.enabled:
        return True, "stopped"

    if context.scheduler_worker_service is None:
        return False, "missing"

    if context.scheduler_worker_service.is_running:
        return True, "running"

    if context.is_running:
        return False, "stopped"

    return True, "stopped"


def _plugin_health(context: ApplicationContext) -> tuple[bool, str]:
    """Summarize plugin loading status for health checks."""
    if not context.settings.config.strategy.auto_load:
        return True, "auto_load=false"

    if context.plugin_manager is None:
        return False, "plugin manager missing"

    report = context.plugin_load_report
    if report is None:
        return True, "loaded=unknown"

    return True, (
        f"loaded={len(report.loaded)}, skipped={len(report.skipped)}, errors={len(report.errors)}"
    )
