"""Staff dashboard routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from auth.jwt_config import get_tenant, require_role
from core.tenancy import Tenant
from db.session import get_db
from models.enums import UserRole
from models.user import User
from schemas.appointment import AppointmentRead
from schemas.dashboard import DashboardSummary
from services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

require_staff = require_role(UserRole.ADMIN, UserRole.BARBER)


@router.get(
    "/summary",
    response_model=DashboardSummary,
    summary="Return today's operational figures",
)
async def get_summary(
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(require_staff),
) -> DashboardSummary:
    """Return real figures scoped to the caller's role."""
    return await DashboardService(db, tenant).get_summary(current_user)


@router.get(
    "/today",
    response_model=list[AppointmentRead],
    summary="Return every appointment scheduled for today",
)
async def get_today(
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(require_staff),
) -> list[AppointmentRead]:
    """Return today's agenda for the caller."""
    return await DashboardService(db, tenant).list_today(current_user)
