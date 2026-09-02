"""SQLAlchemy async engine configuration."""

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from core.config import get_settings
from models.base import Base

settings = get_settings()

engine = create_async_engine(
    settings.async_database_url,
    echo=settings.sql_echo,
    **(
        {}
        if settings.async_database_url.startswith("sqlite")
        else {
            "max_overflow": settings.postgres_max_overflow,
            "pool_pre_ping": settings.postgres_pool_pre_ping,
            "pool_size": settings.postgres_pool_size,
        }
    ),
)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def create_all_tables() -> None:
    """Create all tables. Prefer Alembic outside quick local smoke checks."""
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def check_database_connection() -> bool:
    """Return True when the configured database is reachable."""
    from sqlalchemy import text

    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
    return True
