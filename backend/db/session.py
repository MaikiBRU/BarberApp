"""Database session dependency."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from db.database import SessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session and handle transaction cleanup."""
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
