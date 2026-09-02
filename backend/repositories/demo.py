"""Data access for portfolio demo sandboxes."""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.demo import DemoSession
from repositories.base import BaseRepository


class DemoSessionRepository(BaseRepository[DemoSession]):
    """Sandbox lifecycle rows.

    Demo sessions are the tenant registry itself, so they are the one
    table that is deliberately not tenant-scoped.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize repository for the DemoSession model."""
        super().__init__(db, DemoSession)

    async def get_active(
        self,
        session_id: str,
        *,
        now: datetime,
        idle_cutoff: datetime,
    ) -> DemoSession | None:
        """Return a sandbox only while it is still usable.

        Expiry is checked on every request rather than trusting the
        cleanup job to have already run.
        """
        statement = (
            select(DemoSession)
            .where(DemoSession.id == session_id)
            .where(DemoSession.revoked.is_(False))
            .where(DemoSession.expires_at > now)
            .where(DemoSession.last_seen_at > idle_cutoff)
        )
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def count_active(self, *, now: datetime) -> int:
        """Return how many sandboxes are currently alive."""
        statement = (
            select(func.count())
            .select_from(DemoSession)
            .where(DemoSession.revoked.is_(False))
            .where(DemoSession.expires_at > now)
        )
        result = await self.db.execute(statement)
        return int(result.scalar_one())

    async def list_expired(self, *, now: datetime) -> list[DemoSession]:
        """Return sandboxes whose data can be removed."""
        statement = select(DemoSession).where(
            (DemoSession.expires_at <= now) | DemoSession.revoked.is_(True)
        )
        result = await self.db.execute(statement)
        return list(result.scalars().all())
