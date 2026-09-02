"""Database-backed availability calculation for the booking engine."""

from datetime import UTC, date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from core.tenancy import Tenant
from exceptions.errors import NotFoundError, ValidationError
from models.service import ProductExtra, Service
from models.user import BarberProfile
from repositories.appointments import AppointmentRepository
from repositories.catalog import ProductExtraRepository, ServiceRepository
from repositories.schedule import BusinessHoursRepository, TimeOffRepository
from repositories.users import BarberRepository
from schemas.booking import (
    AvailabilityQuery,
    AvailabilityResponse,
    BarberSlots,
    DaySlot,
)
from services.availability import TimeRange, compute_available_starts


class AvailabilityService:
    """Resolve which start times a barber can actually take."""

    def __init__(
        self,
        db: AsyncSession,
        tenant: Tenant | None = None,
    ) -> None:
        """Wire the repositories the availability query depends on."""
        self.db = db
        self.tenant = tenant or Tenant.real()
        self.settings = get_settings()
        self.appointments = AppointmentRepository(db, self.tenant)
        self.services = ServiceRepository(db, self.tenant)
        self.extras = ProductExtraRepository(db, self.tenant)
        self.barbers = BarberRepository(db, self.tenant)
        self.hours = BusinessHoursRepository(db, self.tenant)
        self.time_off = TimeOffRepository(db, self.tenant)

    async def get_availability(
        self,
        query: AvailabilityQuery,
    ) -> AvailabilityResponse:
        """Return bookable slots for a service on a given local day."""
        service = await self.require_active_service(query.service_id)
        extras = await self.resolve_extras(query.extra_ids)
        duration = self.total_duration(service, extras)
        slot_minutes = self.settings.booking_slot_minutes

        hours = await self.hours.get_for_weekday(query.date.weekday())
        if hours is None or hours.is_closed:
            return AvailabilityResponse(
                date=query.date,
                service_id=service.id,
                duration_minutes=duration,
                slot_minutes=slot_minutes,
                is_open=False,
                barbers=[],
            )

        profiles = await self.resolve_barbers(query.barber_id)
        starts_by_profile = await self.available_starts(
            profiles,
            day=query.date,
            duration_minutes=duration,
        )

        return AvailabilityResponse(
            date=query.date,
            service_id=service.id,
            duration_minutes=duration,
            slot_minutes=slot_minutes,
            is_open=True,
            barbers=[
                BarberSlots(
                    barber_id=profile.id,
                    barber_user_id=profile.user_id,
                    display_name=profile.display_name,
                    slots=[
                        DaySlot(
                            starts_at=start,
                            ends_at=start + timedelta(minutes=duration),
                        )
                        for start in starts_by_profile.get(profile.id, [])
                    ],
                )
                for profile in profiles
            ],
        )

    async def available_starts(
        self,
        profiles: list[BarberProfile],
        *,
        day: date,
        duration_minutes: int,
    ) -> dict[str, list[datetime]]:
        """Return bookable UTC starts per barber profile id."""
        if not profiles:
            return {}

        hours = await self.hours.get_for_weekday(day.weekday())
        if hours is None or hours.is_closed:
            return {profile.id: [] for profile in profiles}

        window_start, window_end = self.day_bounds_utc(day)
        busy = await self.collect_busy(
            profiles,
            window_start=window_start,
            window_end=window_end,
        )
        earliest, latest = self.booking_horizon()

        return {
            profile.id: compute_available_starts(
                day=day,
                opens_at=hours.opens_at,
                closes_at=hours.closes_at,
                shop_timezone=self.settings.timezone,
                duration_minutes=duration_minutes,
                slot_minutes=self.settings.booking_slot_minutes,
                busy=busy.get(profile.user_id, []),
                earliest_start=earliest,
                latest_start=latest,
            )
            for profile in profiles
        }

    async def require_active_service(self, service_id: str) -> Service:
        """Return a bookable service or raise a typed error."""
        service = await self.services.get_active(service_id)
        if service is None:
            raise NotFoundError("service", service_id)
        return service

    async def resolve_extras(
        self,
        extra_ids: list[str],
    ) -> list[ProductExtra]:
        """Return the requested extras, rejecting unknown or inactive ids."""
        unique_ids = list(dict.fromkeys(extra_ids))
        if not unique_ids:
            return []

        extras = await self.extras.list_active_by_ids(unique_ids)
        if len(extras) != len(unique_ids):
            found = {extra.id for extra in extras}
            raise ValidationError(
                "Alguno de los extras elegidos ya no está disponible.",
                details={
                    "extra_ids": [
                        item for item in unique_ids if item not in found
                    ]
                },
            )
        return extras

    async def resolve_barbers(
        self,
        barber_profile_id: str | None,
    ) -> list[BarberProfile]:
        """Return the bookable barbers a query applies to."""
        if barber_profile_id is None:
            return await self.barbers.list_barbers(active_only=True)

        profile = await self.barbers.get_profile(barber_profile_id)
        if not self.is_bookable(profile):
            raise NotFoundError("barber", barber_profile_id)
        return [profile]

    @staticmethod
    def is_bookable(profile: BarberProfile | None) -> bool:
        """Return True when a barber profile can receive appointments."""
        return bool(
            profile
            and profile.is_active
            and profile.user
            and profile.user.is_active
        )

    @staticmethod
    def total_duration(
        service: Service,
        extras: list[ProductExtra],
    ) -> int:
        """Return the total appointment duration including extras."""
        return service.duration_minutes + sum(
            extra.duration_minutes for extra in extras
        )

    def day_bounds_utc(self, day: date) -> tuple[datetime, datetime]:
        """Return the UTC bounds covering one local calendar day."""
        tz = self.settings.timezone
        start_local = datetime.combine(day, datetime.min.time(), tzinfo=tz)
        end_local = start_local + timedelta(days=1)
        return (
            start_local.astimezone(UTC),
            end_local.astimezone(UTC),
        )

    def booking_horizon(self) -> tuple[datetime, datetime]:
        """Return the earliest and latest bookable start instants."""
        now = datetime.now(UTC)
        return (
            now + timedelta(minutes=self.settings.booking_min_lead_minutes),
            now + timedelta(days=self.settings.booking_max_advance_days),
        )

    async def collect_busy(
        self,
        profiles: list[BarberProfile],
        *,
        window_start: datetime,
        window_end: datetime,
    ) -> dict[str, list[TimeRange]]:
        """Return occupied ranges per barber user id for the window."""
        user_ids = [profile.user_id for profile in profiles]
        profile_ids = [profile.id for profile in profiles]
        user_id_by_profile = {
            profile.id: profile.user_id for profile in profiles
        }

        busy: dict[str, list[TimeRange]] = {
            user_id: [] for user_id in user_ids
        }

        booked = await self.appointments.list_blocking_for_barbers(
            user_ids,
            window_start=window_start,
            window_end=window_end,
        )
        for appointment in booked:
            busy[appointment.barber_id].append(
                TimeRange(
                    start=appointment.starts_at,
                    end=appointment.ends_at,
                )
            )

        absences = await self.time_off.list_for_barbers(
            profile_ids,
            window_start=window_start,
            window_end=window_end,
        )
        for absence in absences:
            busy[user_id_by_profile[absence.barber_id]].append(
                TimeRange(start=absence.starts_at, end=absence.ends_at)
            )

        return busy
