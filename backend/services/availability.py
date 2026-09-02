"""Pure slot-generation logic for the booking engine.

This module holds no database or framework dependencies so the rules
that decide when a barber is bookable can be unit tested directly.
"""

from dataclasses import dataclass
from datetime import (
    UTC,
    date,
    datetime,
    time,
    timedelta,
    tzinfo,
)


@dataclass(frozen=True, slots=True)
class TimeRange:
    """A half-open ``[start, end)`` interval of aware datetimes."""

    start: datetime
    end: datetime

    def overlaps(self, other: "TimeRange") -> bool:
        """Return True when the two intervals share any instant."""
        return self.start < other.end and other.start < self.end

    def contains(self, moment: datetime) -> bool:
        """Return True when the instant falls inside the interval."""
        return self.start <= moment < self.end


@dataclass(frozen=True, slots=True)
class OpeningWindow:
    """The shop opening window for one calendar day, in UTC."""

    opens_at: datetime
    closes_at: datetime


def build_opening_window(
    day: date,
    opens_at: time,
    closes_at: time,
    shop_timezone: tzinfo,
) -> OpeningWindow:
    """Convert wall-clock opening hours into an absolute UTC window.

    Using ``datetime.combine`` with the shop timezone keeps the window
    anchored to local business hours across daylight saving changes.
    """
    local_open = datetime.combine(day, opens_at, tzinfo=shop_timezone)
    local_close = datetime.combine(day, closes_at, tzinfo=shop_timezone)
    return OpeningWindow(
        opens_at=local_open.astimezone(UTC),
        closes_at=local_close.astimezone(UTC),
    )


def generate_slot_starts(
    window: OpeningWindow,
    *,
    duration_minutes: int,
    slot_minutes: int,
) -> list[datetime]:
    """Return every candidate start that fully fits inside the window."""
    if duration_minutes <= 0 or slot_minutes <= 0:
        return []

    duration = timedelta(minutes=duration_minutes)
    step = timedelta(minutes=slot_minutes)
    latest_start = window.closes_at - duration

    starts: list[datetime] = []
    cursor = window.opens_at
    while cursor <= latest_start:
        starts.append(cursor)
        cursor += step
    return starts


def filter_available_starts(
    starts: list[datetime],
    *,
    duration_minutes: int,
    busy: list[TimeRange],
    earliest_start: datetime,
    latest_start: datetime,
) -> list[datetime]:
    """Drop candidates that are too soon, too far out, or occupied."""
    duration = timedelta(minutes=duration_minutes)
    available: list[datetime] = []

    for start in starts:
        if start < earliest_start or start > latest_start:
            continue
        candidate = TimeRange(start=start, end=start + duration)
        if any(candidate.overlaps(taken) for taken in busy):
            continue
        available.append(start)

    return available


def compute_available_starts(
    *,
    day: date,
    opens_at: time,
    closes_at: time,
    shop_timezone: tzinfo,
    duration_minutes: int,
    slot_minutes: int,
    busy: list[TimeRange],
    earliest_start: datetime,
    latest_start: datetime,
) -> list[datetime]:
    """Return bookable UTC start times for one barber on one day."""
    window = build_opening_window(day, opens_at, closes_at, shop_timezone)
    candidates = generate_slot_starts(
        window,
        duration_minutes=duration_minutes,
        slot_minutes=slot_minutes,
    )
    return filter_available_starts(
        candidates,
        duration_minutes=duration_minutes,
        busy=busy,
        earliest_start=earliest_start,
        latest_start=latest_start,
    )

