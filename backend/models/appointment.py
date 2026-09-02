"""Appointment and payment models."""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, new_id
from models.enums import (
    AppointmentStatus,
    PaymentMethod,
    PaymentStatus,
    enum_values,
)
from models.service import ProductExtra, Service
from models.types import UTCDateTime
from models.user import User

appointment_extras = Table(
    "appointment_extras",
    Base.metadata,
    Column(
        "appointment_id",
        ForeignKey("appointments.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "extra_id",
        ForeignKey("product_extras.id", ondelete="RESTRICT"),
        primary_key=True,
    ),
    Column("price_cents", Integer, nullable=False, server_default="0"),
)


class Appointment(TimestampMixin, Base):
    """Booked customer appointment.

    ``ends_at`` is stored rather than derived so the database can index
    and range-check the occupied window. PostgreSQL additionally gets an
    exclusion constraint (see the migrations) that makes overlapping
    bookings for the same barber impossible at the storage layer.
    """

    __tablename__ = "appointments"
    __table_args__ = (
        CheckConstraint(
            "duration_minutes > 0",
            name="ck_appointments_duration_positive",
        ),
        CheckConstraint(
            "ends_at > starts_at",
            name="ck_appointments_window",
        ),
        CheckConstraint(
            "tip_cents >= 0",
            name="ck_appointments_tip_non_negative",
        ),
        CheckConstraint(
            "service_price_cents >= 0 AND extras_price_cents >= 0",
            name="ck_appointments_prices_non_negative",
        ),
        CheckConstraint(
            "customer_id <> barber_id",
            name="ck_appointments_distinct_parties",
        ),
        Index("ix_appointments_barber_starts", "barber_id", "starts_at"),
        Index("ix_appointments_customer_starts", "customer_id", "starts_at"),
        Index("ix_appointments_status_starts", "status", "starts_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=new_id,
    )
    shop_id: Mapped[str | None] = mapped_column(
        String(64),
        index=True,
        nullable=True,
    )
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    barber_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    service_id: Mapped[str] = mapped_column(
        ForeignKey("services.id", ondelete="RESTRICT"),
        nullable=False,
    )
    starts_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    ends_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(
            AppointmentStatus,
            name="appointment_status",
            values_callable=enum_values,
        ),
        default=AppointmentStatus.PENDING,
        nullable=False,
    )
    service_price_cents: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    extras_price_cents: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    payment_method: Mapped[PaymentMethod | None] = mapped_column(
        Enum(PaymentMethod, name="payment_method", values_callable=enum_values),
        nullable=True,
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status", values_callable=enum_values),
        default=PaymentStatus.PENDING,
        nullable=False,
    )
    tip_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        UTCDateTime,
        nullable=True,
    )

    customer: Mapped[User] = relationship(foreign_keys=[customer_id])
    barber: Mapped[User] = relationship(foreign_keys=[barber_id])
    service: Mapped[Service] = relationship()
    extras: Mapped[list[ProductExtra]] = relationship(
        secondary=appointment_extras,
    )
    payment: Mapped["Payment | None"] = relationship(
        back_populates="appointment",
        cascade="all, delete-orphan",
        uselist=False,
    )

    @property
    def total_price_cents(self) -> int:
        """Return the booked total including extras and tip."""
        return (
            self.service_price_cents
            + self.extras_price_cents
            + self.tip_cents
        )


class Payment(TimestampMixin, Base):
    """Payment record for an appointment."""

    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint(
            "amount_cents >= 0 AND tip_cents >= 0",
            name="ck_payments_amounts_non_negative",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=new_id,
    )
    appointment_id: Mapped[str] = mapped_column(
        ForeignKey("appointments.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, name="payment_method", values_callable=enum_values),
        nullable=False,
    )
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status", values_callable=enum_values),
        default=PaymentStatus.PENDING,
        nullable=False,
    )
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    tip_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    external_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    appointment: Mapped[Appointment] = relationship(back_populates="payment")
