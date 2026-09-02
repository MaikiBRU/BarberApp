"""Appointment creation on top of the availability engine."""

from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.tenancy import Tenant
from exceptions.errors import (
    BusinessRuleError,
    NotFoundError,
    SlotUnavailableError,
)
from models.appointment import Appointment
from models.enums import PaymentMethod
from repositories.appointments import AppointmentRepository
from repositories.users import UserRepository
from services.availability_service import AvailabilityService


class BookingService:
    """Turn a chosen slot into a persisted appointment.

    Every rule the availability endpoint applies is re-checked here, so a
    client that skips the availability call, replays a stale slot, or
    races another customer still cannot create an invalid booking.
    """

    def __init__(
        self,
        db: AsyncSession,
        tenant: Tenant | None = None,
    ) -> None:
        """Wire the availability engine and the write repositories."""
        self.db = db
        self.tenant = tenant or Tenant.real()
        self.availability = AvailabilityService(db, self.tenant)
        self.appointments = AppointmentRepository(db, self.tenant)
        self.users = UserRepository(db, self.tenant)

    async def create_appointment(
        self,
        *,
        customer_id: str,
        barber_user_id: str,
        service_id: str,
        starts_at: datetime,
        extra_ids: list[str],
        notes: str | None = None,
        payment_method: PaymentMethod | None = None,
    ) -> Appointment:
        """Validate the request end to end and persist the appointment."""
        service = await self.availability.require_active_service(service_id)
        extras = await self.availability.resolve_extras(extra_ids)
        duration = self.availability.total_duration(service, extras)

        barber_profile = await self.availability.barbers.get_by_user_id(
            barber_user_id
        )
        if not self.availability.is_bookable(barber_profile):
            raise NotFoundError("barber", barber_user_id)

        customer = await self.users.get_by_id(customer_id)
        if customer is None or not customer.is_active:
            raise NotFoundError("customer", customer_id)
        if customer.id == barber_user_id:
            raise BusinessRuleError(
                "Un barbero no puede reservarse un turno consigo mismo.",
            )

        await self._assert_slot_bookable(
            barber_profile=barber_profile,
            starts_at=starts_at,
            duration_minutes=duration,
        )

        appointment = Appointment(
            shop_id=self.tenant.shop_id,
            customer_id=customer.id,
            barber_id=barber_user_id,
            service_id=service.id,
            starts_at=starts_at,
            ends_at=starts_at + timedelta(minutes=duration),
            duration_minutes=duration,
            service_price_cents=service.price_cents,
            extras_price_cents=sum(extra.price_cents for extra in extras),
            payment_method=payment_method,
            notes=notes or None,
        )
        appointment.extras.extend(extras)
        self.db.add(appointment)

        try:
            await self.db.flush()
        except IntegrityError as exc:
            # PostgreSQL rejects overlaps through an EXCLUDE constraint,
            # which closes the window between the check above and the
            # insert when two customers book the same slot at once.
            raise SlotUnavailableError() from exc

        return await self._reload(appointment.id)

    async def _reload(self, appointment_id: str) -> Appointment:
        """Return the stored appointment with its relations loaded."""
        appointment = await self.appointments.get_detail(appointment_id)
        if appointment is None:
            raise NotFoundError("appointment", appointment_id)
        return appointment

    async def _assert_slot_bookable(
        self,
        *,
        barber_profile,
        starts_at: datetime,
        duration_minutes: int,
    ) -> None:
        """Re-run every availability rule for the exact requested slot."""
        settings = self.availability.settings
        earliest, latest = self.availability.booking_horizon()

        if starts_at < earliest:
            raise BusinessRuleError(
                "Los turnos se reservan con al menos "
                f"{settings.booking_min_lead_minutes} minutos de "
                "anticipación.",
            )
        if starts_at > latest:
            raise BusinessRuleError(
                "No se pueden reservar turnos con más de "
                f"{settings.booking_max_advance_days} días de "
                "anticipación.",
            )

        local_day = starts_at.astimezone(settings.timezone).date()
        allowed = await self.availability.available_starts(
            [barber_profile],
            day=local_day,
            duration_minutes=duration_minutes,
        )
        if starts_at not in allowed.get(barber_profile.id, []):
            raise SlotUnavailableError()
