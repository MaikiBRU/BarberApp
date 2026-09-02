"""Unit tests for the pure slot-generation rules."""

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from services.availability import (
    TimeRange,
    build_opening_window,
    compute_available_starts,
    filter_available_starts,
    generate_slot_starts,
)

SHOP_TZ = ZoneInfo("America/Argentina/Buenos_Aires")
DAY = date(2026, 9, 10)
FAR_PAST = datetime(2000, 1, 1, tzinfo=UTC)
FAR_FUTURE = datetime(2100, 1, 1, tzinfo=UTC)


def test_opening_window_is_anchored_to_local_wall_clock() -> None:
    """09:00 local becomes the matching UTC instant for that date."""
    window = build_opening_window(DAY, time(9, 0), time(19, 0), SHOP_TZ)

    assert window.opens_at.tzinfo is UTC
    assert window.opens_at.astimezone(SHOP_TZ).hour == 9
    assert window.closes_at.astimezone(SHOP_TZ).hour == 19


def test_slots_never_run_past_closing_time() -> None:
    """The last start leaves room for the full service duration."""
    window = build_opening_window(DAY, time(9, 0), time(10, 0), SHOP_TZ)

    starts = generate_slot_starts(
        window,
        duration_minutes=45,
        slot_minutes=15,
    )

    assert len(starts) == 2
    assert starts[0] == window.opens_at
    assert starts[-1] + timedelta(minutes=45) <= window.closes_at


def test_longer_service_yields_fewer_slots() -> None:
    """Service duration drives how many starts fit in the day."""
    window = build_opening_window(DAY, time(9, 0), time(12, 0), SHOP_TZ)

    short = generate_slot_starts(
        window,
        duration_minutes=30,
        slot_minutes=30,
    )
    long = generate_slot_starts(
        window,
        duration_minutes=90,
        slot_minutes=30,
    )

    assert len(short) == 6
    assert len(long) == 4


def test_busy_ranges_remove_overlapping_starts() -> None:
    """A booked range hides every candidate that would collide."""
    window = build_opening_window(DAY, time(9, 0), time(12, 0), SHOP_TZ)
    starts = generate_slot_starts(
        window,
        duration_minutes=60,
        slot_minutes=30,
    )
    booked = TimeRange(
        start=window.opens_at + timedelta(minutes=30),
        end=window.opens_at + timedelta(minutes=90),
    )

    available = filter_available_starts(
        starts,
        duration_minutes=60,
        busy=[booked],
        earliest_start=FAR_PAST,
        latest_start=FAR_FUTURE,
    )

    assert available == [
        window.opens_at + timedelta(minutes=90),
        window.opens_at + timedelta(minutes=120),
    ]


def test_lead_time_and_horizon_bound_the_results() -> None:
    """Starts before the lead time or past the horizon are dropped."""
    window = build_opening_window(DAY, time(9, 0), time(12, 0), SHOP_TZ)
    starts = generate_slot_starts(
        window,
        duration_minutes=30,
        slot_minutes=60,
    )

    available = filter_available_starts(
        starts,
        duration_minutes=30,
        busy=[],
        earliest_start=starts[1],
        latest_start=starts[1],
    )

    assert available == [starts[1]]


def test_back_to_back_bookings_are_allowed() -> None:
    """An appointment ending exactly when the next starts is fine."""
    window = build_opening_window(DAY, time(9, 0), time(11, 0), SHOP_TZ)
    booked = TimeRange(
        start=window.opens_at,
        end=window.opens_at + timedelta(minutes=60),
    )

    available = compute_available_starts(
        day=DAY,
        opens_at=time(9, 0),
        closes_at=time(11, 0),
        shop_timezone=SHOP_TZ,
        duration_minutes=60,
        slot_minutes=60,
        busy=[booked],
        earliest_start=FAR_PAST,
        latest_start=FAR_FUTURE,
    )

    assert available == [window.opens_at + timedelta(minutes=60)]


def test_time_range_overlap_is_half_open() -> None:
    """Touching intervals do not overlap; crossing intervals do."""
    base = datetime(2026, 9, 10, 12, 0, tzinfo=UTC)
    first = TimeRange(start=base, end=base + timedelta(minutes=30))
    touching = TimeRange(
        start=base + timedelta(minutes=30),
        end=base + timedelta(minutes=60),
    )
    crossing = TimeRange(
        start=base + timedelta(minutes=29),
        end=base + timedelta(minutes=60),
    )

    assert not first.overlaps(touching)
    assert first.overlaps(crossing)


def test_no_slots_when_window_is_shorter_than_the_service() -> None:
    """A service that cannot fit produces an empty list."""
    window = build_opening_window(DAY, time(9, 0), time(9, 30), SHOP_TZ)

    assert generate_slot_starts(
        window,
        duration_minutes=45,
        slot_minutes=15,
    ) == []
