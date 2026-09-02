"""Authentication DTOs."""

from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

from models.enums import UserRole
from schemas.user import UserRead


class RegisterRequest(BaseModel):
    """Request body for public account registration.

    ``role`` is pinned to ``customer``: privileged accounts are created
    by an administrator or the CLI, never by self-service signup.
    """

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Literal[UserRole.CUSTOMER] = UserRole.CUSTOMER
    full_name: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=40)

    @field_validator("full_name", "phone")
    @classmethod
    def blank_to_none(cls, value: str | None) -> str | None:
        """Treat whitespace-only optional fields as absent."""
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class LoginRequest(BaseModel):
    """Request body for email/password login."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    """JWT access token response."""

    access_token: str
    token_type: Literal["bearer"] = "bearer"  # noqa: S105
    expires_in: int = Field(description="Token lifetime in seconds")
    user: UserRead
