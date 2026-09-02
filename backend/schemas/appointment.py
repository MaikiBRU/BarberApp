"""Appointment DTOs."""

from datetime import datetime

from pydantic import EmailStr, Field, field_validator

from models.enums import AppointmentStatus, PaymentMethod, PaymentStatus
from schemas.base import BaseSchema


class AppointmentCreate(BaseSchema):
    """Shape a customer submits to book a slot.

    Neither the customer id nor the duration is accepted from the
    client: the owner comes from the access token and the duration is
    derived from the service and its extras. That removes both an IDOR
    and a mass-assignment vector.
    """

    barber_id: str = Field(description="User id of the barber")
    service_id: str
    starts_at: datetime
    extra_ids: list[str] = Field(default_factory=list, max_length=10)
    payment_method: PaymentMethod | None = None
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("starts_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        """Reject naive timestamps so the instant is unambiguous."""
        if value.tzinfo is None:
            raise ValueError("starts_at must include a timezone offset")
        return value

    @field_validator("notes")
    @classmethod
    def clean_notes(cls, value: str | None) -> str | None:
        """Treat whitespace-only notes as absent."""
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class AdminAppointmentCreate(AppointmentCreate):
    """Admin variant that may book on behalf of an existing customer."""

    customer_id: str


class AppointmentStatusUpdate(BaseSchema):
    """Input for moving an appointment to another lifecycle state."""

    status: AppointmentStatus
    cancellation_reason: str | None = Field(default=None, max_length=255)


class PartySummary(BaseSchema):
    """Minimal identity block for the customer or the barber.

    Contact details are populated only for viewers entitled to see them,
    which keeps a customer from reading another person's phone number.
    """

    id: str
    name: str
    email: EmailStr | None = None
    phone: str | None = None


class ServiceSummary(BaseSchema):
    """Service snapshot shown inside an appointment."""

    id: str
    name: str
    duration_minutes: int
    price_cents: int


class ExtraSummary(BaseSchema):
    """Extra snapshot shown inside an appointment."""

    id: str
    name: str
    price_cents: int


class AppointmentRead(BaseSchema):
    """Appointment representation returned by the API."""

    id: str
    customer: PartySummary
    barber: PartySummary
    service: ServiceSummary
    extras: list[ExtraSummary]
    starts_at: datetime
    ends_at: datetime
    duration_minutes: int
    status: AppointmentStatus
    service_price_cents: int
    extras_price_cents: int
    tip_cents: int
    total_price_cents: int
    payment_method: PaymentMethod | None = None
    payment_status: PaymentStatus
    notes: str | None = None
    cancellation_reason: str | None = None
    cancelled_at: datetime | None = None
    created_at: datetime
    can_cancel: bool = Field(
        description="Whether the current viewer may cancel this booking.",
    )
    allowed_transitions: list[AppointmentStatus] = Field(
        default_factory=list,
        description="States the current viewer may move this booking to.",
    )
