"""Service and extra product models."""

from sqlalchemy import Boolean, CheckConstraint, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, TimestampMixin, new_id


class Service(TimestampMixin, Base):
    """Bookable barbershop service."""

    __tablename__ = "services"
    __table_args__ = (
        CheckConstraint(
            "duration_minutes > 0",
            name="ck_services_duration_positive",
        ),
        CheckConstraint(
            "price_cents >= 0",
            name="ck_services_price_non_negative",
        ),
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
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )


class ProductExtra(TimestampMixin, Base):
    """Optional product or add-on attached to appointments."""

    __tablename__ = "product_extras"
    __table_args__ = (
        CheckConstraint(
            "duration_minutes >= 0",
            name="ck_extras_duration_non_negative",
        ),
        CheckConstraint(
            "price_cents >= 0",
            name="ck_extras_price_non_negative",
        ),
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
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )
