"""Appointment reading and lifecycle transitions."""

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.errors import (
    AuthorizationError,
    BusinessRuleError,
    NotFoundError,
    ValidationError,
)
from models.appointment import Appointment
from models.enums import STATUS_TRANSITIONS, AppointmentStatus, UserRole
from models.user import User
from repositories.appointments import AppointmentRepository
from schemas.appointment import AppointmentRead, AppointmentStatusUpdate
from schemas.base import Page
from services.appointment_view import (
    allowed_transitions,
    can_view,
    is_owner,
    to_read,
)


class AppointmentService:
    """Read and transition appointments under role-based rules."""

    def __init__(self, db: AsyncSession) -> None:
        """Wire the appointment repository."""
        self.db = db
        self.appointments = AppointmentRepository(db)

    async def list_for_viewer(
        self,
        viewer: User,
        *,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        statuses: list[AppointmentStatus] | None = None,
        barber_id: str | None = None,
        customer_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
        newest_first: bool = False,
    ) -> Page[AppointmentRead]:
        """Return the appointments the viewer is entitled to see.

        Scoping happens in the query, not in the response, so a customer
        can never read another customer's bookings by paging past them.
        """
        scoped_customer, scoped_barber = self._scope_filters(
            viewer,
            barber_id=barber_id,
            customer_id=customer_id,
        )

        rows, total = await self.appointments.search(
            customer_id=scoped_customer,
            barber_id=scoped_barber,
            date_from=date_from,
            date_to=date_to,
            statuses=statuses,
            limit=limit,
            offset=offset,
            newest_first=newest_first,
        )
        return Page[AppointmentRead](
            items=[
                to_read(appointment, viewer)
                for appointment in rows
            ],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_for_viewer(
        self,
        appointment_id: str,
        viewer: User,
    ) -> AppointmentRead:
        """Return one appointment when the viewer may read it."""
        appointment = await self._require_visible(appointment_id, viewer)
        return to_read(appointment, viewer)

    async def update_status(
        self,
        appointment_id: str,
        data: AppointmentStatusUpdate,
        viewer: User,
    ) -> AppointmentRead:
        """Move an appointment to another state when the rules allow it."""
        appointment = await self._require_visible(appointment_id, viewer)
        self._assert_transition_allowed(appointment, data.status, viewer)

        changes: dict[str, object] = {"status": data.status}
        if data.status == AppointmentStatus.CANCELLED:
            changes["cancelled_at"] = datetime.now(UTC)
            changes["cancellation_reason"] = data.cancellation_reason
        elif data.cancellation_reason:
            raise ValidationError(
                "A cancellation reason only applies when cancelling.",
            )

        updated = await self.appointments.update(appointment, changes)
        detail = await self.appointments.get_detail(updated.id)
        return to_read(detail or updated, viewer)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    @staticmethod
    def _scope_filters(
        viewer: User,
        *,
        barber_id: str | None,
        customer_id: str | None,
    ) -> tuple[str | None, str | None]:
        """Return the customer and barber filters the viewer may use."""
        if viewer.role == UserRole.ADMIN:
            return customer_id, barber_id
        if viewer.role == UserRole.BARBER:
            # A barber sees their own agenda and may narrow it by
            # customer; the barber filter is pinned to themselves.
            return customer_id, viewer.id

        # A customer is pinned to their own bookings. A barber filter is
        # harmless here because it only narrows rows they already own.
        return viewer.id, barber_id

    async def _require_visible(
        self,
        appointment_id: str,
        viewer: User,
    ) -> Appointment:
        """Return an appointment the viewer may read, or raise."""
        appointment = await self.appointments.get_detail(appointment_id)
        if appointment is None:
            raise NotFoundError("Appointment", appointment_id)
        if not can_view(appointment, viewer):
            # Report 404 rather than 403 so the endpoint does not confirm
            # that an appointment with this id exists.
            raise NotFoundError("Appointment", appointment_id)
        return appointment

    @staticmethod
    def _assert_transition_allowed(
        appointment: Appointment,
        next_status: AppointmentStatus,
        viewer: User,
    ) -> None:
        """Enforce the state machine and the per-role permissions."""
        if next_status == appointment.status:
            raise BusinessRuleError(
                f"The appointment is already {next_status.value}.",
            )

        reachable = STATUS_TRANSITIONS.get(appointment.status, frozenset())
        if not reachable:
            raise BusinessRuleError(
                f"A {appointment.status.value} appointment is final.",
            )
        if next_status not in reachable:
            raise BusinessRuleError(
                f"Cannot move an appointment from "
                f"{appointment.status.value} to {next_status.value}.",
            )

        allowed = allowed_transitions(appointment, viewer)
        if next_status in allowed:
            return

        if (
            next_status == AppointmentStatus.CANCELLED
            and viewer.role == UserRole.CUSTOMER
            and is_owner(appointment, viewer)
        ):
            raise BusinessRuleError(
                "This booking is too close to its start time to be "
                "cancelled online. Contact the shop instead.",
            )

        raise AuthorizationError()
