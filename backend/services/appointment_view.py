"""Viewer-aware serialization of appointments.

Which contact details appear in a response depends on who is asking.
Keeping that decision here means every endpoint returning an
appointment enforces the same privacy rules.
"""

from datetime import UTC, datetime

from core.config import get_settings
from models.appointment import Appointment
from models.enums import (
    BLOCKING_STATUSES,
    STATUS_TRANSITIONS,
    AppointmentStatus,
    UserRole,
)
from models.user import User
from schemas.appointment import (
    AppointmentRead,
    ExtraSummary,
    PartySummary,
    ServiceSummary,
)

#: Transitions each role may request, before per-appointment ownership
#: and timing rules are applied.
ROLE_TRANSITIONS: dict[UserRole, frozenset[AppointmentStatus]] = {
    UserRole.ADMIN: frozenset(AppointmentStatus),
    UserRole.BARBER: frozenset(
        {
            AppointmentStatus.CONFIRMED,
            AppointmentStatus.COMPLETED,
            AppointmentStatus.CANCELLED,
            AppointmentStatus.NO_SHOW,
        }
    ),
    UserRole.CUSTOMER: frozenset({AppointmentStatus.CANCELLED}),
}


def is_owner(appointment: Appointment, viewer: User) -> bool:
    """Return True when the viewer booked the appointment."""
    return appointment.customer_id == viewer.id


def is_assigned_barber(appointment: Appointment, viewer: User) -> bool:
    """Return True when the viewer is the barber on the appointment."""
    return appointment.barber_id == viewer.id


def can_view(appointment: Appointment, viewer: User) -> bool:
    """Return True when the viewer may read the appointment at all."""
    if viewer.role == UserRole.ADMIN:
        return True
    return is_owner(appointment, viewer) or is_assigned_barber(
        appointment,
        viewer,
    )


def can_cancel(appointment: Appointment, viewer: User) -> bool:
    """Return True when the viewer may cancel right now."""
    if appointment.status not in BLOCKING_STATUSES:
        return False

    if viewer.role == UserRole.ADMIN:
        return True
    if is_assigned_barber(appointment, viewer):
        return True
    if not is_owner(appointment, viewer):
        return False

    cutoff_minutes = get_settings().booking_cancellation_cutoff_minutes
    remaining = appointment.starts_at - datetime.now(UTC)
    return remaining.total_seconds() >= cutoff_minutes * 60


def allowed_transitions(
    appointment: Appointment,
    viewer: User,
) -> list[AppointmentStatus]:
    """Return the states this viewer may move the appointment to."""
    reachable = STATUS_TRANSITIONS.get(appointment.status, frozenset())
    if not reachable:
        return []

    by_role = ROLE_TRANSITIONS.get(viewer.role, frozenset())
    if viewer.role == UserRole.BARBER and not is_assigned_barber(
        appointment,
        viewer,
    ):
        by_role = frozenset()
    if viewer.role == UserRole.CUSTOMER and not is_owner(appointment, viewer):
        by_role = frozenset()

    allowed = reachable & by_role
    if AppointmentStatus.CANCELLED in allowed and not can_cancel(
        appointment,
        viewer,
    ):
        allowed -= {AppointmentStatus.CANCELLED}

    return sorted(allowed, key=lambda status: status.value)


def _party(
    user: User,
    *,
    name: str,
    include_contact: bool,
    phone: str | None,
) -> PartySummary:
    """Build a party block, redacting contact details when needed."""
    return PartySummary(
        id=user.id,
        name=name,
        email=user.email if include_contact else None,
        phone=phone if include_contact else None,
    )


def to_read(appointment: Appointment, viewer: User) -> AppointmentRead:
    """Serialize an appointment for one specific viewer."""
    is_admin = viewer.role == UserRole.ADMIN
    assigned = is_assigned_barber(appointment, viewer)

    customer = appointment.customer
    customer_profile = customer.customer_profile
    customer_name = (
        customer_profile.full_name
        if customer_profile and customer_profile.full_name
        else customer.email
    )

    barber = appointment.barber
    barber_profile = barber.barber_profile
    barber_name = (
        barber_profile.display_name if barber_profile else barber.email
    )

    return AppointmentRead(
        id=appointment.id,
        customer=_party(
            customer,
            name=customer_name,
            include_contact=is_admin or assigned,
            phone=customer_profile.phone if customer_profile else None,
        ),
        barber=_party(
            barber,
            name=barber_name,
            include_contact=is_admin,
            phone=barber_profile.phone if barber_profile else None,
        ),
        service=ServiceSummary.model_validate(appointment.service),
        extras=[
            ExtraSummary.model_validate(extra) for extra in appointment.extras
        ],
        starts_at=appointment.starts_at,
        ends_at=appointment.ends_at,
        duration_minutes=appointment.duration_minutes,
        status=appointment.status,
        service_price_cents=appointment.service_price_cents,
        extras_price_cents=appointment.extras_price_cents,
        tip_cents=appointment.tip_cents,
        total_price_cents=appointment.total_price_cents,
        payment_method=appointment.payment_method,
        payment_status=appointment.payment_status,
        notes=appointment.notes,
        cancellation_reason=appointment.cancellation_reason,
        cancelled_at=appointment.cancelled_at,
        created_at=appointment.created_at,
        can_cancel=can_cancel(appointment, viewer),
        allowed_transitions=allowed_transitions(appointment, viewer),
    )
