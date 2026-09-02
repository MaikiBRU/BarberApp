"""Unit tests for the authentication throttle."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from middleware.exception_handler import register_exception_handlers
from middleware.rate_limit import RateLimitMiddleware, SlidingWindowCounter


def test_counter_allows_up_to_the_limit() -> None:
    """The first N requests inside the window pass."""
    counter = SlidingWindowCounter(max_requests=3, window_seconds=60)

    results = [counter.check("ip", now=0.0 + step) for step in range(3)]

    assert results == [None, None, None]


def test_counter_blocks_the_request_after_the_limit() -> None:
    """The next request reports how long the caller must wait."""
    counter = SlidingWindowCounter(max_requests=2, window_seconds=60)
    counter.check("ip", now=0.0)
    counter.check("ip", now=1.0)

    retry_after = counter.check("ip", now=2.0)

    assert retry_after is not None
    assert 0 < retry_after <= 60


def test_counter_forgets_hits_older_than_the_window() -> None:
    """Once the window slides past, the allowance is restored."""
    counter = SlidingWindowCounter(max_requests=1, window_seconds=10)
    counter.check("ip", now=0.0)

    assert counter.check("ip", now=5.0) is not None
    assert counter.check("ip", now=11.0) is None


def test_counter_tracks_each_key_separately() -> None:
    """One client hitting the limit does not affect another."""
    counter = SlidingWindowCounter(max_requests=1, window_seconds=60)
    counter.check("first", now=0.0)

    assert counter.check("second", now=0.0) is None


def test_middleware_throttles_the_login_endpoint() -> None:
    """Repeated login attempts eventually return 429."""
    app = FastAPI()
    register_exception_handlers(app)
    app.add_middleware(
        RateLimitMiddleware,
        max_requests=2,
        window_seconds=60,
    )

    @app.post("/api/v1/auth/login")
    async def login() -> dict[str, bool]:
        return {"ok": True}

    with TestClient(app) as client:
        statuses = [
            client.post("/api/v1/auth/login").status_code for _ in range(3)
        ]

    assert statuses == [200, 200, 429]


def test_middleware_leaves_other_paths_untouched() -> None:
    """Only the credential endpoints are throttled."""
    app = FastAPI()
    register_exception_handlers(app)
    app.add_middleware(
        RateLimitMiddleware,
        max_requests=1,
        window_seconds=60,
    )

    @app.get("/api/v1/catalog/services")
    async def services() -> list[str]:
        return []

    with TestClient(app) as client:
        statuses = [
            client.get("/api/v1/catalog/services").status_code
            for _ in range(3)
        ]

    assert statuses == [200, 200, 200]
