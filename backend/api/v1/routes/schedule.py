"""Opening hours and barber time-off routes."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.jwt_config import get_current_user, require_role
from db.session import get_db
from exceptions.errors import AuthorizationError
from models.enums import UserRole
from models.user import User
from schemas.schedule import (
    BusinessHoursRead,
    TimeOffCreate,
    TimeOffRead,
    WeeklyHoursUpdate,
)
from services.schedule_service import ScheduleService
from services.user_service import UserService

router = APIRouter(prefix="/schedule", tags=["schedule"])

require_admin = require_role(UserRole.ADMIN)


async def _assert_can_manage_barber(
    db: AsyncSession,
    barber_id: str,
    user: User,
) -> None:
    """Allow admins, or a barber acting on their own agenda."""
    if user.role == UserRole.ADMIN:
        return
    if user.role != UserRole.BARBER:
        raise AuthorizationError()

    profile = await UserService(db).get_barber_profile_for_user(user)
    if profile.id != barber_id:
        raise AuthorizationError()


@router.get(
    "/business-hours",
    response_model=list[BusinessHoursRead],
    summary="Return the weekly opening schedule",
)
async def list_business_hours(
    db: AsyncSession = Depends(get_db),
) -> list[BusinessHoursRead]:
    """Return the opening window for each weekday."""
    return await ScheduleService(db).list_business_hours()


@router.put(
    "/business-hours",
    response_model=list[BusinessHoursRead],
    summary="Replace the weekly opening schedule",
)
async def update_business_hours(
    payload: WeeklyHoursUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[BusinessHoursRead]:
    """Upsert the submitted weekdays. Administrators only."""
    return await ScheduleService(db).replace_business_hours(payload)


@router.get(
    "/barbers/{barber_id}/time-off",
    response_model=list[TimeOffRead],
    summary="Return upcoming time off for a barber",
)
async def list_time_off(
    barber_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TimeOffRead]:
    """Return the absences blocking a barber agenda."""
    await _assert_can_manage_barber(db, barber_id, current_user)
    return await ScheduleService(db).list_time_off(barber_id)


@router.post(
    "/barbers/{barber_id}/time-off",
    response_model=TimeOffRead,
    status_code=status.HTTP_201_CREATED,
    summary="Block a window in a barber agenda",
)
async def create_time_off(
    barber_id: str,
    payload: TimeOffCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TimeOffRead:
    """Create an absence so the slot stops being offered."""
    await _assert_can_manage_barber(db, barber_id, current_user)
    return await ScheduleService(db).create_time_off(barber_id, payload)


@router.delete(
    "/barbers/{barber_id}/time-off/{time_off_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a time-off entry",
)
async def delete_time_off(
    barber_id: str,
    time_off_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete an absence entry."""
    await _assert_can_manage_barber(db, barber_id, current_user)
    await ScheduleService(db).delete_time_off(barber_id, time_off_id)
