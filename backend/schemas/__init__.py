"""Shared API schemas."""

from schemas.appointment import (
    AdminAppointmentCreate,
    AppointmentCreate,
    AppointmentRead,
    AppointmentStatusUpdate,
    ExtraSummary,
    PartySummary,
    ServiceSummary,
)
from schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from schemas.base import BaseSchema, Page
from schemas.booking import (
    AvailabilityQuery,
    AvailabilityResponse,
    BarberSlots,
    DaySlot,
)
from schemas.dashboard import AppointmentCounts, DashboardSummary
from schemas.schedule import (
    BusinessHoursRead,
    BusinessHoursWrite,
    TimeOffCreate,
    TimeOffRead,
    WeeklyHoursUpdate,
)
from schemas.service import (
    ProductExtraCreate,
    ProductExtraRead,
    ProductExtraUpdate,
    ServiceCreate,
    ServiceRead,
    ServiceUpdate,
)
from schemas.user import (
    BarberCreate,
    BarberRead,
    BarberUpdate,
    CustomerProfileRead,
    CustomerProfileUpdate,
    UserRead,
)

__all__ = [
    "AdminAppointmentCreate",
    "AppointmentCounts",
    "AppointmentCreate",
    "AppointmentRead",
    "AppointmentStatusUpdate",
    "AvailabilityQuery",
    "AvailabilityResponse",
    "BarberCreate",
    "BarberRead",
    "BarberSlots",
    "BarberUpdate",
    "BaseSchema",
    "BusinessHoursRead",
    "BusinessHoursWrite",
    "CustomerProfileRead",
    "CustomerProfileUpdate",
    "DashboardSummary",
    "DaySlot",
    "ExtraSummary",
    "LoginRequest",
    "Page",
    "PartySummary",
    "ProductExtraCreate",
    "ProductExtraRead",
    "ProductExtraUpdate",
    "RegisterRequest",
    "ServiceCreate",
    "ServiceRead",
    "ServiceSummary",
    "ServiceUpdate",
    "TimeOffCreate",
    "TimeOffRead",
    "TokenResponse",
    "UserRead",
    "WeeklyHoursUpdate",
]
