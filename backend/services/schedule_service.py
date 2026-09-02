"""Opening hours and barber time-off business logic."""

from datetime import UTC, datetime, time

from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.errors import BusinessRuleError, NotFoundError
from models.schedule import BusinessHours
from repositories.schedule import BusinessHoursRepository, TimeOffRepository
from repositories.users import BarberRepository
from schemas.schedule import (
    BusinessHoursRead,
    TimeOffCreate,
    TimeOffRead,
    WeeklyHoursUpdate,
)


class ScheduleService:
    """Manage the weekly opening schedule and barber absences."""

    def __init__(self, db: AsyncSession) -> None:
        """Wire the schedule repositories."""
        self.db = db
        self.hours = BusinessHoursRepository(db)
        self.time_off = TimeOffRepository(db)
        self.barbers = BarberRepository(db)

    async def list_business_hours(self) -> list[BusinessHoursRead]:
        """Return the weekly opening schedule."""
        rows = await self.hours.list_week()
        return [BusinessHoursRead.model_validate(row) for row in rows]

    async def replace_business_hours(
        self,
        data: WeeklyHoursUpdate,
    ) -> list[BusinessHoursRead]:
        """Upsert the submitted weekdays into the opening schedule."""
        for day in data.days:
            existing = await self.hours.get_for_weekday(day.weekday)
            values = {
                "opens_at": day.opens_at,
                "closes_at": day.closes_at,
                "is_closed": day.is_closed,
            }
            if existing is None:
                await self.hours.create(
                    {"weekday": day.weekday, **values},
                )
            else:
                await self.hours.update(existing, values)

        return await self.list_business_hours()

    async def list_time_off(self, barber_profile_id: str) -> list[TimeOffRead]:
        """Return upcoming absences for one barber."""
        await self._require_barber(barber_profile_id)
        rows = await self.time_off.list_upcoming(
            barber_profile_id,
            since=datetime.now(UTC),
        )
        return [TimeOffRead.model_validate(row) for row in rows]

    async def create_time_off(
        self,
        barber_profile_id: str,
        data: TimeOffCreate,
    ) -> TimeOffRead:
        """Block a window in a barber agenda."""
        await self._require_barber(barber_profile_id)

        overlapping = await self.time_off.list_for_barbers(
            [barber_profile_id],
            window_start=data.starts_at,
            window_end=data.ends_at,
        )
        if overlapping:
            raise BusinessRuleError(
                "That window overlaps an existing time-off entry.",
            )

        created = await self.time_off.create(
            {
                "barber_id": barber_profile_id,
                "starts_at": data.starts_at,
                "ends_at": data.ends_at,
                "reason": data.reason,
            }
        )
        return TimeOffRead.model_validate(created)

    async def delete_time_off(
        self,
        barber_profile_id: str,
        time_off_id: str,
    ) -> None:
        """Remove an absence entry."""
        entry = await self.time_off.get_by_id(time_off_id)
        if entry is None or entry.barber_id != barber_profile_id:
            raise NotFoundError("Time off", time_off_id)
        await self.time_off.delete(entry)

    async def _require_barber(self, barber_profile_id: str) -> None:
        """Raise when the barber profile does not exist."""
        if await self.barbers.get_profile(barber_profile_id) is None:
            raise NotFoundError("Barber", barber_profile_id)


#: Opening schedule seeded for local development, in shop local time.
DEFAULT_WEEK: tuple[tuple[int, str, str, bool], ...] = (
    (0, "09:00", "19:00", False),
    (1, "09:00", "19:00", False),
    (2, "09:00", "19:00", False),
    (3, "09:00", "20:00", False),
    (4, "09:00", "20:00", False),
    (5, "09:00", "17:00", False),
    (6, "09:00", "13:00", True),
)


def default_business_hours() -> list[BusinessHours]:
    """Return the seeded opening schedule used for local development."""
    return [
        BusinessHours(
            weekday=weekday,
            opens_at=time.fromisoformat(opens),
            closes_at=time.fromisoformat(closes),
            is_closed=closed,
        )
        for weekday, opens, closes, closed in DEFAULT_WEEK
    ]
