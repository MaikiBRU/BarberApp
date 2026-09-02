"""User, barber and profile routes."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.jwt_config import get_current_user, require_role
from db.session import get_db
from models.enums import UserRole
from models.user import User
from schemas.user import (
    BarberCreate,
    BarberRead,
    BarberUpdate,
    CustomerProfileRead,
    CustomerProfileUpdate,
)
from services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])

require_admin = require_role(UserRole.ADMIN)


@router.get(
    "/barbers",
    response_model=list[BarberRead],
    summary="List barbers available for booking",
)
async def list_barbers(
    db: AsyncSession = Depends(get_db),
) -> list[BarberRead]:
    """Return active barbers without exposing their contact details."""
    return await UserService(db).list_barbers()


@router.get(
    "/admin/barbers",
    response_model=list[BarberRead],
    summary="List every barber, including deactivated ones",
)
async def list_barbers_admin(
    include_inactive: bool = Query(default=True),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[BarberRead]:
    """Return every barber with contact details. Administrators only."""
    return await UserService(db).list_barbers(
        include_inactive=include_inactive,
        include_contact=True,
    )


@router.post(
    "/barbers",
    response_model=BarberRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a barber account",
)
async def create_barber(
    payload: BarberCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> BarberRead:
    """Create a barber account and profile. Administrators only."""
    return await UserService(db).create_barber(payload)


@router.patch(
    "/barbers/{barber_id}",
    response_model=BarberRead,
    summary="Update a barber profile",
)
async def update_barber(
    barber_id: str,
    payload: BarberUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> BarberRead:
    """Update a barber profile. Administrators only."""
    return await UserService(db).update_barber(barber_id, payload)


@router.get(
    "/me/profile",
    response_model=CustomerProfileRead,
    summary="Return the authenticated customer profile",
)
async def get_my_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CustomerProfileRead:
    """Return the profile attached to the authenticated account."""
    return await UserService(db).get_customer_profile(current_user)


@router.patch(
    "/me/profile",
    response_model=CustomerProfileRead,
    summary="Update the authenticated customer profile",
)
async def update_my_profile(
    payload: CustomerProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CustomerProfileRead:
    """Update the profile attached to the authenticated account."""
    return await UserService(db).update_customer_profile(
        current_user,
        payload,
    )
