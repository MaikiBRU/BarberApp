"""Service catalog DTOs."""

from datetime import datetime

from pydantic import Field, field_validator

from schemas.base import BaseSchema


class ServiceCreate(BaseSchema):
    """Input for creating a bookable service.

    ``shop_id`` is deliberately absent: it is assigned by the server so
    a client cannot attach a record to another shop.
    """

    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    duration_minutes: int = Field(gt=0, le=480)
    price_cents: int = Field(ge=0)

    @field_validator("name")
    @classmethod
    def trim_name(cls, value: str) -> str:
        """Normalize surrounding whitespace."""
        return value.strip()


class ServiceUpdate(BaseSchema):
    """Input for updating a bookable service."""

    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    duration_minutes: int | None = Field(default=None, gt=0, le=480)
    price_cents: int | None = Field(default=None, ge=0)
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def trim_name(cls, value: str | None) -> str | None:
        """Normalize surrounding whitespace."""
        return value.strip() if value else value


class ServiceRead(BaseSchema):
    """Public service representation."""

    id: str
    shop_id: str | None = None
    name: str
    description: str | None = None
    duration_minutes: int
    price_cents: int
    is_active: bool
    created_at: datetime


class ProductExtraCreate(BaseSchema):
    """Input for creating an appointment add-on."""

    name: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    price_cents: int = Field(ge=0)
    duration_minutes: int = Field(default=0, ge=0, le=240)

    @field_validator("name")
    @classmethod
    def trim_name(cls, value: str) -> str:
        """Normalize surrounding whitespace."""
        return value.strip()


class ProductExtraUpdate(BaseSchema):
    """Input for updating an appointment add-on."""

    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    price_cents: int | None = Field(default=None, ge=0)
    duration_minutes: int | None = Field(default=None, ge=0, le=240)
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def trim_name(cls, value: str | None) -> str | None:
        """Normalize surrounding whitespace."""
        return value.strip() if value else value


class ProductExtraRead(BaseSchema):
    """Public product extra representation."""

    id: str
    shop_id: str | None = None
    name: str
    description: str | None = None
    price_cents: int
    duration_minutes: int
    is_active: bool
    created_at: datetime
