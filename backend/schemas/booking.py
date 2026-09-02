"""Availability DTOs for the booking flow."""

import datetime

from pydantic import Field

from schemas.base import BaseSchema


class AvailabilityQuery(BaseSchema):
    """Parameters that define one availability lookup."""

    date: datetime.date
    service_id: str
    barber_id: str | None = Field(
        default=None,
        description="Barber profile id. Omit to query every active barber.",
    )
    extra_ids: list[str] = Field(default_factory=list)


class DaySlot(BaseSchema):
    """A single bookable time range, in UTC."""

    starts_at: datetime.datetime
    ends_at: datetime.datetime


class BarberSlots(BaseSchema):
    """Every slot one barber can take on the requested day."""

    barber_id: str
    barber_user_id: str
    display_name: str
    slots: list[DaySlot]


class AvailabilityResponse(BaseSchema):
    """Availability for one service on one local calendar day."""

    date: datetime.date
    service_id: str
    duration_minutes: int = Field(
        description="Service duration plus the duration of every extra.",
    )
    slot_minutes: int = Field(description="Spacing of the slot grid.")
    is_open: bool = Field(description="False when the shop is closed.")
    barbers: list[BarberSlots]
