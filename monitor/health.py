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
    interval: int = 60  # increased from 30s - no need to hammer endpoints so frequently
    timeout: int = 10   # seconds before timeout
    expected_status: int = 200
    retries: int = 3    # bumped from 2 - one extra retry before marking down


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
                    logger.debug("[%s] client error, retrying (%d/%d): %s", config.name, attempt + 1, config.retries, exc)
                    continue
                return CheckResult(
                    status=HealthStatus.DOWN,
                    error=str(exc),
                )
