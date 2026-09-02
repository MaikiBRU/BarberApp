"""Authentication routes."""

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from auth.jwt_config import get_current_user, get_tenant
from core.tenancy import Tenant
from db.session import get_db
from models.user import User
from schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from schemas.user import UserRead
from services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a customer account",
)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
) -> TokenResponse:
    """Create a customer account and return an access token."""
    return await AuthService(db, tenant).register(payload)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in with email and password",
)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
) -> TokenResponse:
    """Authenticate a user and return an access token."""
    return await AuthService(db, tenant).login(payload)


@router.post(
    "/token",
    response_model=TokenResponse,
    include_in_schema=False,
    summary="OAuth2 password flow used by the interactive docs",
)
async def token(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
) -> TokenResponse:
    """Issue a token from form credentials so Swagger can authorize."""
    return await AuthService(db, tenant).login(
        LoginRequest(email=form.username, password=form.password),
    )


@router.get(
    "/me",
    response_model=UserRead,
    summary="Return the authenticated account",
)
async def me(current_user: User = Depends(get_current_user)) -> User:
    """Return the account behind the bearer token."""
    return current_user
