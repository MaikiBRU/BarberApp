"""JWT creation and FastAPI authentication dependencies."""

from collections.abc import Callable, Coroutine
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from core.tenancy import Tenant
from db.session import get_db
from exceptions.errors import AuthenticationError, AuthorizationError
from models.enums import UserRole
from models.user import User
from repositories.demo import DemoSessionRepository
from repositories.users import UserRepository

TOKEN_TYPE_ACCESS = "access"  # noqa: S105  (claim value, not a secret)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/token",
    auto_error=False,
)


class TokenPayload(BaseModel):
    """Decoded JWT payload."""

    sub: str
    typ: str = TOKEN_TYPE_ACCESS
    email: str | None = None
    role: UserRole | None = None
    jti: str | None = None
    #: Demo sandbox this token is scoped to. Absent for real accounts.
    shop: str | None = None


def create_access_token(
    subject: str,
    additional_claims: dict[str, Any] | None = None,
    expires_at: datetime | None = None,
) -> str:
    """Create a signed access token for a user id.

    ``expires_at`` caps the lifetime, which the demo uses so a sandbox
    token can never outlive the sandbox itself.
    """
    settings = get_settings()
    now = datetime.now(UTC)
    default_expiry = now + timedelta(
        minutes=settings.jwt_access_token_expire_minutes,
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "typ": TOKEN_TYPE_ACCESS,
        "jti": uuid4().hex,
        "iat": now,
        "exp": (
            min(default_expiry, expires_at)
            if expires_at
            else default_expiry
        ),
    }
    if additional_claims:
        payload.update(additional_claims)

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> TokenPayload:
    """Decode and validate an access token.

    ``algorithms`` is pinned to the configured algorithm so a forged
    header cannot downgrade verification.
    """
    settings = get_settings()
    try:
        claims = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        payload = TokenPayload.model_validate(claims)
    except (JWTError, ValueError) as exc:
        raise AuthenticationError() from exc

    if payload.typ != TOKEN_TYPE_ACCESS:
        raise AuthenticationError()
    return payload


async def get_tenant(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Tenant:
    """Resolve which shop the request may touch.

    Anonymous callers and real accounts get the real shop. A token
    carrying a ``shop`` claim gets that demo sandbox, but only while the
    sandbox is still alive: expiry is enforced here, on every request.
    """
    if not token:
        return Tenant.real()

    try:
        payload = decode_token(token)
    except AuthenticationError:
        # Public endpoints stay readable with a stale token in hand.
        return Tenant.real()

    if not payload.shop:
        return Tenant.real()

    session = await _active_demo_session(db, payload.shop)
    if session is None:
        raise AuthenticationError(
            "La sesión de demo expiró. Iniciá una nueva.",
        )
    return Tenant.demo(session.id)


async def _active_demo_session(db: AsyncSession, session_id: str):
    """Return a live sandbox and refresh its idle timer."""
    settings = get_settings()
    now = datetime.now(UTC)
    idle_cutoff = now - timedelta(
        minutes=settings.demo_idle_timeout_minutes,
    )

    repository = DemoSessionRepository(db)
    session = await repository.get_active(
        session_id,
        now=now,
        idle_cutoff=idle_cutoff,
    )
    if session is not None:
        session.last_seen_at = now
        await db.flush()
    return session


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    tenant: Tenant = Depends(get_tenant),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Return the authenticated user behind the bearer token.

    The lookup is scoped to the token's tenant, so a demo token can only
    ever resolve to a user inside its own sandbox.
    """
    if not token:
        raise AuthenticationError("Necesitás iniciar sesión.")

    payload = decode_token(token)
    if (payload.shop or None) != tenant.shop_id:
        raise AuthenticationError()

    user = await UserRepository(db, tenant).get_with_profiles(payload.sub)
    if user is None or not user.is_active:
        raise AuthenticationError()
    return user


async def get_optional_user(
    token: str | None = Depends(oauth2_scheme),
    tenant: Tenant = Depends(get_tenant),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Return the authenticated user, or None for anonymous callers."""
    if not token:
        return None
    try:
        return await get_current_user(token=token, tenant=tenant, db=db)
    except AuthenticationError:
        return None


def require_role(
    *roles: UserRole,
) -> Callable[..., Coroutine[Any, Any, User]]:
    """Create a dependency that allows only the listed roles.

    Role checks live here, on the server, and never trust a claim the
    frontend sends: the role is read from the database row every time.
    """
    allowed = frozenset(roles)

    async def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise AuthorizationError()
        return user

    return dependency


async def require_auth(user: User = Depends(get_current_user)) -> User:
    """Require any authenticated user."""
    return user

