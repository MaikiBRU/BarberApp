"""Public entry point for the portfolio demo sandbox.

``POST /demo/session`` is the only unauthenticated write in the demo
surface. It mints a sandbox, seeds it with a working barbershop, and
returns a token scoped to that sandbox and to one persona inside it.
"""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.jwt_config import create_access_token, get_current_user, get_tenant
from core.config import get_settings
from core.tenancy import Tenant
from db.session import get_db
from exceptions.errors import AuthenticationError, NotFoundError
from models.enums import UserRole
from models.user import User
from repositories.demo import DemoSessionRepository
from repositories.users import UserRepository
from schemas.demo import (
    DemoConfig,
    DemoLimits,
    DemoPersona,
    DemoRoleRequest,
    DemoSessionRead,
    DemoSessionState,
    DemoStartResponse,
)
from schemas.user import UserRead
from services import demo_service
from services.demo_seed import seed_sandbox

router = APIRouter(prefix="/demo", tags=["demo"])

PERSONAS = (
    DemoPersona(
        role=UserRole.CUSTOMER,
        label="Cliente",
        description="Reservá un turno y gestioná tus reservas.",
    ),
    DemoPersona(
        role=UserRole.BARBER,
        label="Barbero",
        description="Mirá tu agenda del día y cambiá estados de turnos.",
    ),
    DemoPersona(
        role=UserRole.ADMIN,
        label="Administrador",
        description="Gestioná servicios, extras, barberos y horarios.",
    ),
)


def _limits() -> DemoLimits:
    """Return the configured sandbox caps."""
    settings = get_settings()
    return DemoLimits(
        session_ttl_minutes=settings.demo_session_ttl_minutes,
        idle_timeout_minutes=settings.demo_idle_timeout_minutes,
        max_appointments=settings.demo_max_appointments,
        max_writes=settings.demo_max_writes,
    )


def _client_ip(request: Request) -> str | None:
    """Return the caller address, preferring the first forwarded hop."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def _read(session, role: UserRole) -> DemoSessionRead:
    """Build the payload the demo chrome polls."""
    state = demo_service.describe(session)
    return DemoSessionRead(
        state=DemoSessionState(
            label=state.label,
            expires_at=state.expires_at,
            seconds_remaining=state.seconds_remaining,
            idle_seconds_remaining=state.idle_seconds_remaining,
            appointments_used=state.appointments_used,
            appointments_max=state.appointments_max,
            writes_used=state.writes_used,
            writes_max=state.writes_max,
            active_role=role,
        ),
        limits=_limits(),
        personas=list(PERSONAS),
    )


def _issue(session, user: User) -> DemoStartResponse:
    """Mint a sandbox token that cannot outlive its sandbox."""
    token = create_access_token(
        subject=user.id,
        additional_claims={
            "email": user.email,
            "role": user.role.value,
            "shop": session.id,
        },
        expires_at=session.expires_at,
    )
    remaining = int(
        (session.expires_at - datetime.now(UTC)).total_seconds()
    )
    return DemoStartResponse(
        access_token=token,
        expires_in=max(remaining, 0),
        user=UserRead.model_validate(user),
        session=_read(session, user.role),
    )


async def require_demo(
    tenant: Tenant = Depends(get_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Return the live sandbox behind the caller's token."""
    if not tenant.is_demo or tenant.shop_id is None:
        raise AuthenticationError("Esta acción requiere una sesión de demo.")

    settings = get_settings()
    now = datetime.now(UTC)
    session = await DemoSessionRepository(db).get_active(
        tenant.shop_id,
        now=now,
        idle_cutoff=now
        - timedelta(minutes=settings.demo_idle_timeout_minutes),
    )
    if session is None:
        raise AuthenticationError("La sesión de demo expiró.")
    return session


async def _persona_user(
    db: AsyncSession,
    session,
    role: UserRole,
) -> User:
    """Return the seeded account for one persona of a sandbox."""
    tenant = Tenant.demo(session.id)
    users = UserRepository(db, tenant)

    candidates = await users.list(limit=50)
    for user in sorted(candidates, key=lambda item: item.email):
        if user.role == role:
            return user
    raise NotFoundError("customer" if role == UserRole.CUSTOMER else "barber")


@router.get(
    "/config",
    response_model=DemoConfig,
    summary="Public demo configuration",
)
async def demo_config() -> DemoConfig:
    """Let the landing page render the limits without a sandbox."""
    settings = get_settings()
    return DemoConfig(
        enabled=settings.demo_enabled,
        limits=_limits(),
        personas=list(PERSONAS),
    )


@router.post(
    "/session",
    response_model=DemoStartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a sandbox and get a token for it",
)
async def start_demo_session(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> DemoStartResponse:
    """Mint a sandbox seeded with a working barbershop."""
    session = await demo_service.create_session(
        db,
        client_ip=_client_ip(request),
    )

    try:
        personas = await seed_sandbox(db, session)
    except Exception:
        # Never hand back a half-built sandbox, and leave nothing behind.
        await db.rollback()
        raise

    visitor = await UserRepository(
        db,
        Tenant.demo(session.id),
    ).get_with_profiles(personas.customer_id)
    if visitor is None:
        raise NotFoundError("customer")
    return _issue(session, visitor)


@router.get(
    "/session",
    response_model=DemoSessionRead,
    summary="Read the live sandbox status",
)
async def read_demo_session(
    session=Depends(require_demo),
    current_user: User = Depends(get_current_user),
) -> DemoSessionRead:
    """Return quotas and time remaining for the demo chrome."""
    return _read(session, current_user.role)


@router.post(
    "/session/role",
    response_model=DemoStartResponse,
    summary="Switch persona inside the same sandbox",
)
async def switch_demo_role(
    payload: DemoRoleRequest,
    session=Depends(require_demo),
    db: AsyncSession = Depends(get_db),
) -> DemoStartResponse:
    """Return a token for another seeded role in this sandbox.

    This is the demo's whole point: the same data seen from the three
    sides of the product without registering three accounts.
    """
    user = await _persona_user(db, session, payload.role)
    return _issue(session, user)


@router.post(
    "/session/reset",
    response_model=DemoStartResponse,
    summary="Wipe the sandbox and seed it again",
)
async def reset_demo_session(
    session=Depends(require_demo),
    db: AsyncSession = Depends(get_db),
) -> DemoStartResponse:
    """Give the visitor a clean sandbox without losing their session."""
    await demo_service.purge_session_data(db, session.id)
    personas = await seed_sandbox(db, session)
    await demo_service.reset_counters(db, session)

    visitor = await UserRepository(
        db,
        Tenant.demo(session.id),
    ).get_with_profiles(personas.customer_id)
    if visitor is None:
        raise NotFoundError("customer")
    return _issue(session, visitor)


@router.post(
    "/session/end",
    summary="Delete the sandbox and everything in it",
)
async def end_demo_session(
    session=Depends(require_demo),
    db: AsyncSession = Depends(get_db),
) -> dict[str, int | str]:
    """Let a visitor wipe their sandbox instead of waiting for expiry."""
    removed = await demo_service.end_session(db, session)
    return {"status": "ended", "removed": removed}
