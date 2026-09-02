"""Operational dashboard DTOs."""

import datetime

from pydantic import Field

from schemas.appointment import AppointmentRead
from schemas.base import BaseSchema


class AppointmentCounts(BaseSchema):
    """Appointment totals for one period, grouped by status."""

    pending: int = 0
    confirmed: int = 0
    completed: int = 0
    cancelled: int = 0
    no_show: int = 0

    @property
    def total(self) -> int:
        """Return the sum of every status bucket."""
        return (
            self.pending
            + self.confirmed
            + self.completed
            + self.cancelled
            + self.no_show
        )


class DashboardSummary(BaseSchema):
    """Real operational figures computed from the database.

    Every field here is derived from stored rows. Metrics that cannot be
    computed from the current domain are simply absent rather than
    invented.
    """

    date: datetime.date = Field(
        description="Local shop date the figures cover",
    )
    today: AppointmentCounts
    upcoming_count: int = Field(
        ge=0,
        description="Active appointments after today.",
    )
    today_revenue_cents: int = Field(
        ge=0,
        description="Booked value of appointments completed today.",
    )
    month_revenue_cents: int = Field(
        ge=0,
        description="Booked value of appointments completed this month.",
    )
    active_barbers: int = Field(ge=0)
    active_services: int = Field(ge=0)
    currency: str
    next_appointments: list[AppointmentRead] = Field(
        default_factory=list,
        description="The next few active appointments for the viewer.",
    )
