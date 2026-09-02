"""Custom SQLAlchemy column types."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator


class UTCDateTime(TypeDecorator[datetime]):
    """Always persist and return timezone-aware UTC datetimes.

    PostgreSQL keeps the offset in ``timestamptz`` but SQLite does not,
    so a SQLite-backed development run would otherwise hand back naive
    datetimes and break every comparison against ``datetime.now(utc)``.
    This decorator normalizes both dialects to aware UTC values.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(
        self,
        value: datetime | None,
        dialect: Dialect,
    ) -> datetime | None:
        """Reject naive input and normalize to UTC before storing."""
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError(
                "Naive datetime rejected; provide a timezone-aware value.",
            )
        return value.astimezone(UTC)

    def process_result_value(
        self,
        value: Any,
        dialect: Dialect,
    ) -> datetime | None:
        """Attach UTC to values loaded from dialects without offsets."""
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
