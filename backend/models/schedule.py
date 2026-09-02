"""Shop opening hours and barber availability exceptions."""

from datetime import datetime, time
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, new_id
from models.types import UTCDateTime

if TYPE_CHECKING:
    from models.user import BarberProfile


class BusinessHours(TimestampMixin, Base):
    """Opening window for one weekday of the shop."""

    __tablename__ = "business_hours"
    __table_args__ = (
        UniqueConstraint("shop_id", "weekday", name="uq_business_hours_day"),
        CheckConstraint(
            "weekday >= 0 AND weekday <= 6",
            name="ck_business_hours_weekday",
        ),
        CheckConstraint(
            "is_closed OR opens_at < closes_at",
            name="ck_business_hours_window",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=new_id,
    )
    shop_id: Mapped[str | None] = mapped_column(
        String(36),
        index=True,
        nullable=True,
    )
    weekday: Mapped[int] = mapped_column(Integer, nullable=False)
    opens_at: Mapped[time] = mapped_column(Time, nullable=False)
    closes_at: Mapped[time] = mapped_column(Time, nullable=False)
    is_closed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )


class BarberTimeOff(TimestampMixin, Base):
    """A window where a barber is unavailable (holiday, break, sick)."""

    __tablename__ = "barber_time_off"
    __table_args__ = (
        CheckConstraint(
            "starts_at < ends_at",
            name="ck_barber_time_off_window",
        ),
        Index("ix_barber_time_off_barber_start", "barber_id", "starts_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=new_id,
    )
    barber_id: Mapped[str] = mapped_column(
        ForeignKey("barber_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    starts_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    ends_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    barber: Mapped["BarberProfile"] = relationship(back_populates="time_off")
