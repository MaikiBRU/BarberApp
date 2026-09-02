"""User and profile models."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, new_id
from models.enums import UserRole, enum_values

if TYPE_CHECKING:
    from models.schedule import BarberTimeOff


class User(TimestampMixin, Base):
    """Authenticated account for admins, barbers, and customers."""

    __tablename__ = "users"

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
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", values_callable=enum_values),
        default=UserRole.CUSTOMER,
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    barber_profile: Mapped["BarberProfile | None"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    customer_profile: Mapped["CustomerProfile | None"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )

    @property
    def display_name(self) -> str:
        """Return the best human-readable name available."""
        if self.barber_profile and self.barber_profile.display_name:
            return self.barber_profile.display_name
        if self.customer_profile and self.customer_profile.full_name:
            return self.customer_profile.full_name
        return self.email


class BarberProfile(TimestampMixin, Base):
    """Operational profile for a barber account."""

    __tablename__ = "barber_profiles"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=new_id,
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="barber_profile")
    time_off: Mapped[list["BarberTimeOff"]] = relationship(
        back_populates="barber",
        cascade="all, delete-orphan",
    )


class CustomerProfile(TimestampMixin, Base):
    """Profile data for customer accounts."""

    __tablename__ = "customer_profiles"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=new_id,
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    full_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship(back_populates="customer_profile")
