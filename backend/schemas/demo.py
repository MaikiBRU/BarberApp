"""DTOs for the portfolio demo sandbox."""

from datetime import datetime

from pydantic import Field

from models.enums import UserRole
from schemas.base import BaseSchema
from schemas.user import UserRead


class DemoLimits(BaseSchema):
    """Caps a sandbox enforces, shown on the landing page."""

    session_ttl_minutes: int
    idle_timeout_minutes: int
    max_appointments: int
    max_writes: int


class DemoPersona(BaseSchema):
    """One role the visitor can step into inside their sandbox."""

    role: UserRole
    label: str
    description: str


class DemoSessionState(BaseSchema):
    """Live sandbox status. Never carries the session id."""

    label: str
    expires_at: datetime
    seconds_remaining: int
    idle_seconds_remaining: int
    appointments_used: int
    appointments_max: int
    writes_used: int
    writes_max: int
    active_role: UserRole


class DemoSessionRead(BaseSchema):
    """Everything the demo chrome needs on each poll."""

    state: DemoSessionState
    limits: DemoLimits
    personas: list[DemoPersona]


class DemoStartResponse(BaseSchema):
    """Response to creating or switching a sandbox persona."""

    access_token: str
    token_type: str = "bearer"  # noqa: S105
    expires_in: int
    user: UserRead
    session: DemoSessionRead


class DemoRoleRequest(BaseSchema):
    """Ask for a token bound to another persona in the same sandbox."""

    role: UserRole


class DemoConfig(BaseSchema):
    """Public configuration, readable without a sandbox."""

    enabled: bool
    limits: DemoLimits
    personas: list[DemoPersona] = Field(default_factory=list)
