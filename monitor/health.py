"""Health monitoring module for itsUP.

Provides health check functionality for monitored services,
including HTTP endpoint checks, TCP port checks, and status tracking.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Possible health states for a monitored service."""
    UP = "up"
    DOWN = "down"
    UNKNOWN = "unknown"
    DEGRADED = "degraded"


@dataclass
class CheckResult:
    """Result of a single health check."""
    status: HealthStatus
    response_time_ms: Optional[float] = None
    status_code: Optional[int] = None
    error: Optional[str] = None
    checked_at: float = field(default_factory=time.time)

    def is_healthy(self) -> bool:
        return self.status == HealthStatus.UP


@dataclass
class ServiceConfig:
    """Configuration for a monitored service."""
    name: str
    url: str
    interval: int = 30  # seconds between checks
    timeout: int = 10   # seconds before timeout
    expected_status: int = 200
    retries: int = 2


class HealthChecker:
    """Performs health checks against configured service endpoints."""

    def __init__(self, session: aiohttp.ClientSession):
        self._session = session

    async def check_http(self, config: ServiceConfig) -> CheckResult:
        """Perform an HTTP health check against the given service config."""
        start = time.monotonic()
        for attempt in range(config.retries + 1):
            try:
                async with self._session.get(
                    config.url,
                    timeout=aiohttp.ClientTimeout(total=config.timeout),
                    allow_redirects=True,
                ) as resp:
                    elapsed = (time.monotonic() - start) * 1000
                    if resp.status == config.expected_status:
                        return CheckResult(
                            status=HealthStatus.UP,
                            response_time_ms=round(elapsed, 2),
                            status_code=resp.status,
                        )
                    logger.warning(
                        "[%s] unexpected status %d (expected %d)",
                        config.name, resp.status, config.expected_status,
                    )
                    return CheckResult(
                        status=HealthStatus.DEGRADED,
                        response_time_ms=round(elapsed, 2),
                        status_code=resp.status,
                    )
            except asyncio.TimeoutError:
                if attempt < config.retries:
                    logger.debug("[%s] timeout, retrying (%d/%d)", config.name, attempt + 1, config.retries)
                    continue
                return CheckResult(
                    status=HealthStatus.DOWN,
                    error="timeout",
                )
            except aiohttp.ClientError as exc:
                if attempt < config.retries:
                    continue
                return CheckResult(
                    status=HealthStatus.DOWN,
                    error=str(exc),
                )
        # Should not reach here, but satisfy type checker
        return CheckResult(status=HealthStatus.UNKNOWN)


class MonitorLoop:
    """Runs periodic health checks for a collection of services."""

    def __init__(self, services: list[ServiceConfig]):
        self._services = services
        self._results: dict[str, CheckResult] = {}
        self._running = False

    @property
    def results(self) -> dict[str, CheckResult]:
        """Latest check results keyed by service name."""
        return dict(self._results)

    async def _check_service(self, checker: HealthChecker, config: ServiceConfig) -> None:
        result = await checker.check_http(config)
        self._results[config.name] = result
        logger.info(
            "[%s] %s (%.1f ms)",
            config.name,
            result.status.value,
            result.response_time_ms or 0,
        )

    async def run(self) -> None:
        """Start the monitoring loop. Runs until cancelled."""
        self._running = True
        async with aiohttp.ClientSession() as session:
            checker = HealthChecker(session)
            while self._running:
                tasks = [
                    self._check_service(checker, svc)
                    for svc in self._services
                ]
                await asyncio.gather(*tasks, return_exceptions=True)
                await asyncio.sleep(min(svc.interval for svc in self._services))

    def stop(self) -> None:
        """Signal the monitoring loop to stop."""
        self._running = False
