"""Business hours and barber time-off data access."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.tenancy import Tenant
from models.schedule import BarberTimeOff, BusinessHours
from repositories.base import BaseRepository


class BusinessHoursRepository(BaseRepository[BusinessHours]):
    """Data access for the weekly opening schedule."""

    def __init__(self, db: AsyncSession, tenant: Tenant | None = None) -> None:
        """Initialize repository for the BusinessHours model."""
        super().__init__(db, BusinessHours, tenant, BusinessHours.shop_id)

    async def list_week(self) -> list[BusinessHours]:
        """Return the seven weekday rows ordered Monday to Sunday."""
        statement = self.scoped(
            select(BusinessHours).order_by(BusinessHours.weekday)
        )
        result = await self.db.execute(statement)
        return list(result.scalars().all())

    async def get_for_weekday(self, weekday: int) -> BusinessHours | None:
        """Return the opening window for one weekday."""
        statement = self.scoped(
            select(BusinessHours).where(BusinessHours.weekday == weekday)
        )
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()


class TimeOffRepository(BaseRepository[BarberTimeOff]):
    """Data access for barber unavailability windows."""

    def __init__(self, db: AsyncSession, tenant: Tenant | None = None) -> None:
        """Initialize repository for the BarberTimeOff model.

        Time off inherits the tenant of its barber profile, and every
        caller resolves those ids through the scoped barber repository,
        so no extra filter is needed here.
        """
        super().__init__(db, BarberTimeOff, tenant)

    async def list_for_barbers(
        self,
        barber_profile_ids: list[str],
        *,
        window_start: datetime,
        window_end: datetime,
    ) -> list[BarberTimeOff]:
        """Return time off overlapping the requested window."""
        if not barber_profile_ids:
            return []
        statement = (
            select(BarberTimeOff)
            .where(BarberTimeOff.barber_id.in_(barber_profile_ids))
            .where(BarberTimeOff.starts_at < window_end)
            .where(BarberTimeOff.ends_at > window_start)
            .order_by(BarberTimeOff.starts_at)
        )
        result = await self.db.execute(statement)
        return list(result.scalars().all())

    async def list_upcoming(
        self,
        barber_profile_id: str,
        *,
        since: datetime,
    ) -> list[BarberTimeOff]:
        """Return future time off for one barber."""
        statement = (
            select(BarberTimeOff)
            .where(BarberTimeOff.barber_id == barber_profile_id)
            .where(BarberTimeOff.ends_at >= since)
            .order_by(BarberTimeOff.starts_at)
        )
        result = await self.db.execute(statement)
        return list(result.scalars().all())
