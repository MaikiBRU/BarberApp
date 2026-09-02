"""Declarative base and shared model mixins."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from models.types import UTCDateTime


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(UTC)


def new_id() -> str:
    """Return a UUID string for primary keys."""
    return str(uuid4())


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


class TimestampMixin:
    """Created and updated timestamp columns."""

    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        server_default=func.now(),
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        server_default=func.now(),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )
