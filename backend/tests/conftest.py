"""Shared pytest fixtures for the backend test suite."""

import os
import sys
from collections.abc import AsyncGenerator, Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Configure the app before importing it: settings are cached at import
# time, and the shared throttle would otherwise leak between tests.
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("SHOP_TIMEZONE", "America/Argentina/Buenos_Aires")
os.environ.setdefault("BOOKING_SLOT_MINUTES", "15")
os.environ.setdefault("BOOKING_MIN_LEAD_MINUTES", "60")
os.environ.setdefault("BOOKING_CANCELLATION_CUTOFF_MINUTES", "120")

import anyio  # noqa: E402

from db.session import get_db  # noqa: E402
from main import app  # noqa: E402
from models import Base  # noqa: E402
from services import demo_service  # noqa: E402
from tests.factories import ApiHelper, seed_baseline  # noqa: E402

TEST_PASSWORD = "Password123!"


@pytest.fixture(autouse=True)
def reset_demo_rate_limit() -> None:
    """Keep the process-wide sandbox counter from leaking between tests."""
    demo_service.reset_rate_limit()


@pytest.fixture()
def session_factory(
    tmp_path: Path,
) -> Generator[async_sessionmaker[AsyncSession], None, None]:
    """Return a session factory bound to a disposable SQLite database."""
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    )
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def prepare() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    anyio.run(prepare)
    yield factory
    anyio.run(engine.dispose)


@pytest.fixture()
def client(
    session_factory: async_sessionmaker[AsyncSession],
) -> Generator[TestClient, None, None]:
    """Return a TestClient wired to the disposable database."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def api(
    client: TestClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> ApiHelper:
    """Return a seeded API helper: staff, catalog and opening hours."""
    anyio.run(seed_baseline, session_factory)
    return ApiHelper(client)
