"""User, barber and customer profile DTOs."""

from datetime import datetime

from pydantic import EmailStr, Field, field_validator

from models.enums import UserRole
from schemas.base import BaseSchema


def _clean_optional(value: str | None) -> str | None:
    """Return a trimmed value, or None when it is blank."""
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


class UserRead(BaseSchema):
    """Public user representation returned by the auth endpoints."""

    id: str
    email: EmailStr
    role: UserRole
    is_active: bool
    shop_id: str | None = None
    created_at: datetime


class CustomerProfileRead(BaseSchema):
    """Customer profile visible to its owner and to staff."""

    user_id: str
    email: EmailStr
    full_name: str | None = None
    phone: str | None = None


class CustomerProfileUpdate(BaseSchema):
    """Fields a customer may change on their own profile."""

    full_name: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=40)

    @field_validator("full_name", "phone")
    @classmethod
    def clean(cls, value: str | None) -> str | None:
        """Trim optional text fields."""
        return _clean_optional(value)


class BarberRead(BaseSchema):
    """Barber profile used for booking and admin views."""

    id: str
    user_id: str
    display_name: str
    bio: str | None = None
    is_active: bool
    email: EmailStr | None = Field(
        default=None,
        description="Only populated for administrators.",
    )
    phone: str | None = Field(
        default=None,
        description="Only populated for administrators.",
    )


class BarberCreate(BaseSchema):
    """Input for creating a barber account plus its profile."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=2, max_length=120)
    bio: str | None = Field(default=None, max_length=1000)
    phone: str | None = Field(default=None, max_length=40)

    @field_validator("bio", "phone")
    @classmethod
    def clean(cls, value: str | None) -> str | None:
        """Trim optional text fields."""
        return _clean_optional(value)


class BarberUpdate(BaseSchema):
    """Input for updating a barber profile."""

    display_name: str | None = Field(default=None, min_length=2, max_length=120)
    bio: str | None = Field(default=None, max_length=1000)
    phone: str | None = Field(default=None, max_length=40)
    is_active: bool | None = None

    @field_validator("bio", "phone")
    @classmethod
    def clean(cls, value: str | None) -> str | None:
        """Trim optional text fields."""
        return _clean_optional(value)
