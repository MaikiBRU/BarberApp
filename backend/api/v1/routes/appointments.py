"""Appointment and availability routes."""

from datetime import date, datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.deps import demo_booking_guard, demo_write_guard
from auth.jwt_config import get_current_user, get_tenant
from core.tenancy import Tenant
from db.session import get_db
from exceptions.errors import AuthorizationError
from models.enums import AppointmentStatus, UserRole
from models.user import User
from schemas.appointment import (
    AdminAppointmentCreate,
    AppointmentCreate,
    AppointmentRead,
    AppointmentStatusUpdate,
)
from schemas.base import Page
from schemas.booking import AvailabilityQuery, AvailabilityResponse
from services.appointment_service import AppointmentService
from services.appointment_view import to_read
from services.availability_service import AvailabilityService
from services.booking_service import BookingService

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.get(
    "/availability",
    response_model=AvailabilityResponse,
    summary="List bookable slots for a service on one day",
)
async def get_availability(
    service_id: str = Query(description="Service to book"),
    day: date = Query(alias="date", description="Local shop date"),
    barber_id: str | None = Query(
        default=None,
        description="Barber profile id. Omit to query every barber.",
    ),
    extra_ids: list[str] = Query(default_factory=list),
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
) -> AvailabilityResponse:
    """Return the slots a customer can actually book.

    The frontend never invents times: it renders exactly what this
    endpoint returns, and the booking endpoint revalidates the choice.
    """
    return await AvailabilityService(db, tenant).get_availability(
        AvailabilityQuery(
            date=day,
            service_id=service_id,
            barber_id=barber_id,
            extra_ids=extra_ids,
        )
    )


@router.get(
    "",
    response_model=Page[AppointmentRead],
    summary="List appointments visible to the caller",
)
async def list_appointments(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    status_filter: list[AppointmentStatus] | None = Query(default=None),
    barber_id: str | None = None,
    customer_id: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    newest_first: bool = False,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user),
) -> Page[AppointmentRead]:
    """Return a page of appointments scoped to the caller's role."""
    return await AppointmentService(db, tenant).list_for_viewer(
        current_user,
        date_from=date_from,
        date_to=date_to,
        statuses=status_filter,
        barber_id=barber_id,
        customer_id=customer_id,
        limit=limit,
        offset=offset,
        newest_first=newest_first,
    )


@router.get(
    "/{appointment_id}",
    response_model=AppointmentRead,
    summary="Return one appointment",
)
async def get_appointment(
    appointment_id: str,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user),
) -> AppointmentRead:
    """Return an appointment the caller is entitled to read."""
    return await AppointmentService(db, tenant).get_for_viewer(
        appointment_id,
        current_user,
    )


@router.post(
    "",
    response_model=AppointmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Book an appointment",
)
async def create_appointment(
    payload: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user),
    _quota: None = Depends(demo_booking_guard),
) -> AppointmentRead:
    """Book a slot for the authenticated customer.

    The owner is taken from the token, never from the request body.
    """
    if current_user.role == UserRole.BARBER:
        raise AuthorizationError(
            "Los barberos no reservan turnos para sí mismos.",
        )

    appointment = await BookingService(db, tenant).create_appointment(
        customer_id=current_user.id,
        barber_user_id=payload.barber_id,
        service_id=payload.service_id,
        starts_at=payload.starts_at,
        extra_ids=payload.extra_ids,
        notes=payload.notes,
        payment_method=payload.payment_method,
    )
    return to_read(appointment, current_user)


@router.post(
    "/admin",
    response_model=AppointmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Book an appointment on behalf of a customer",
)
async def create_appointment_for_customer(
    payload: AdminAppointmentCreate,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user),
    _quota: None = Depends(demo_booking_guard),
) -> AppointmentRead:
    """Book a slot for another customer. Administrators only."""
    if current_user.role != UserRole.ADMIN:
        raise AuthorizationError()

    appointment = await BookingService(db, tenant).create_appointment(
        customer_id=payload.customer_id,
        barber_user_id=payload.barber_id,
        service_id=payload.service_id,
        starts_at=payload.starts_at,
        extra_ids=payload.extra_ids,
        notes=payload.notes,
        payment_method=payload.payment_method,
    )
    return to_read(appointment, current_user)


@router.patch(
    "/{appointment_id}/status",
    response_model=AppointmentRead,
    summary="Move an appointment to another state",
)
async def update_appointment_status(
    appointment_id: str,
    payload: AppointmentStatusUpdate,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user),
    _quota: None = Depends(demo_write_guard),
) -> AppointmentRead:
    """Apply a state transition the caller is allowed to perform."""
    return await AppointmentService(db, tenant).update_status(
        appointment_id,
        payload,
        current_user,
    )
