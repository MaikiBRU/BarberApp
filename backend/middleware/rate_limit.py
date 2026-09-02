"""In-process rate limiting for authentication endpoints.

The limiter keeps counters in memory, which is correct for a single
API process. A multi-process or multi-node deployment needs a shared
store (Redis); that is documented as a known limitation rather than
silently pretended to work.
"""

import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from middleware.exception_handler import error_response

PROTECTED_PATH_PREFIXES = (
    "/api/v1/auth/login",
    "/api/v1/auth/register",
)


class SlidingWindowCounter:
    """Track request timestamps per key inside a sliding window."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        """Configure the allowance and the observation window."""
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str, now: float) -> int | None:
        """Register a hit; return seconds to wait when over the limit."""
        hits = self._hits[key]
        cutoff = now - self.window_seconds
        while hits and hits[0] <= cutoff:
            hits.popleft()

        if len(hits) >= self.max_requests:
            retry_after = int(hits[0] + self.window_seconds - now) + 1
            return max(retry_after, 1)

        hits.append(now)
        return None

    def reset(self) -> None:
        """Drop all counters. Used by tests."""
        self._hits.clear()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Throttle credential endpoints per client IP."""

    def __init__(
        self,
        app: Callable[..., Awaitable[None]],
        *,
        max_requests: int,
        window_seconds: int,
        path_prefixes: tuple[str, ...] = PROTECTED_PATH_PREFIXES,
    ) -> None:
        """Wire the counter and the protected path list."""
        super().__init__(app)
        self.counter = SlidingWindowCounter(max_requests, window_seconds)
        self.path_prefixes = path_prefixes

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Reject requests that exceed the configured allowance."""
        path = request.url.path
        if not path.startswith(self.path_prefixes):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        retry_after = self.counter.check(
            f"{client_ip}:{path}",
            time.monotonic(),
        )
        if retry_after is not None:
            return error_response(
                429,
                "rate_limit_exceeded",
                "Demasiados intentos. Probá de nuevo en unos minutos.",
                details={"retry_after_seconds": retry_after},
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)
