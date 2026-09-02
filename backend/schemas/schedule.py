"""Opening hours and barber time-off DTOs."""

from datetime import datetime, time

from pydantic import Field, model_validator

from schemas.base import BaseSchema


class BusinessHoursRead(BaseSchema):
    """Opening window for one weekday."""

    weekday: int = Field(ge=0, le=6, description="0 = Monday, 6 = Sunday")
    opens_at: time
    closes_at: time
    is_closed: bool


class BusinessHoursWrite(BaseSchema):
    """Admin input for one weekday of the opening schedule."""

    weekday: int = Field(ge=0, le=6)
    opens_at: time
    closes_at: time
    is_closed: bool = False

    @model_validator(mode="after")
    def check_window(self) -> "BusinessHoursWrite":
        """Reject an open day whose window is empty or inverted."""
        if not self.is_closed and self.opens_at >= self.closes_at:
            raise ValueError("opens_at must be earlier than closes_at")
        return self


class WeeklyHoursUpdate(BaseSchema):
    """Full replacement of the weekly opening schedule."""

    days: list[BusinessHoursWrite] = Field(min_length=1, max_length=7)

    @model_validator(mode="after")
    def check_unique_days(self) -> "WeeklyHoursUpdate":
        """Reject duplicated weekdays in one payload."""
        weekdays = [day.weekday for day in self.days]
        if len(set(weekdays)) != len(weekdays):
            raise ValueError("Each weekday may appear only once")
        return self


class TimeOffRead(BaseSchema):
    """A window where a barber is unavailable."""

    id: str
    barber_id: str
    starts_at: datetime
    ends_at: datetime
    reason: str | None = None


class TimeOffCreate(BaseSchema):
    """Input for blocking time in a barber agenda."""

    starts_at: datetime
    ends_at: datetime
    reason: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def check_window(self) -> "TimeOffCreate":
        """Reject inverted or zero-length windows."""
        if self.starts_at >= self.ends_at:
            raise ValueError("starts_at must be earlier than ends_at")
        if self.starts_at.tzinfo is None or self.ends_at.tzinfo is None:
            raise ValueError("Timestamps must include a timezone offset")
        return self
