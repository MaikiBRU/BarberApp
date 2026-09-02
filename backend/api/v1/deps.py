"""Shared route dependencies.

The demo guards are the only place quotas are enforced. They are no-ops
for the real shop, so a single set of routes serves both audiences.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from auth.jwt_config import get_tenant
from core.tenancy import Tenant
from db.session import get_db
from exceptions.errors import AuthenticationError
from services import demo_service


async def _session_or_none(db: AsyncSession, tenant: Tenant):
    """Return the sandbox behind the tenant, refusing an expired one."""
    if not tenant.is_demo:
        return None
    session = await demo_service.get_active_session(db, tenant)
    if session is None:
        raise AuthenticationError("La sesión de demo expiró.")
    return session


async def demo_write_guard(
    tenant: Tenant = Depends(get_tenant),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Count a modification against the sandbox quota."""
    session = await _session_or_none(db, tenant)
    if session is not None:
        await demo_service.register_write(db, session)


async def demo_booking_guard(
    tenant: Tenant = Depends(get_tenant),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Count a booking against the sandbox quota."""
    session = await _session_or_none(db, tenant)
    if session is not None:
        await demo_service.register_appointment(db, session)
