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
from db.session import get_db
from exceptions.errors import AuthenticationError, AuthorizationError
from models.enums import UserRole
from models.user import User
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


def create_access_token(
    subject: str,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    """Create a signed access token for a user id."""
    settings = get_settings()
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "typ": TOKEN_TYPE_ACCESS,
        "jti": uuid4().hex,
        "iat": now,
        "exp": now
        + timedelta(minutes=settings.jwt_access_token_expire_minutes),
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


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Return the authenticated user behind the bearer token."""
    if not token:
        raise AuthenticationError("Authentication required.")

    payload = decode_token(token)
    user = await UserRepository(db).get_with_profiles(payload.sub)
    if user is None or not user.is_active:
        raise AuthenticationError()
    return user


async def get_optional_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Return the authenticated user, or None for anonymous callers."""
    if not token:
        return None
    try:
        return await get_current_user(token=token, db=db)
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

