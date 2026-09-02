"""Authentication business logic."""

from sqlalchemy.ext.asyncio import AsyncSession

from auth.jwt_config import create_access_token
from auth.password_utils import PasswordUtils
from core.config import get_settings
from exceptions.errors import AuthenticationError, ConflictError
from models.enums import UserRole
from models.user import User
from repositories.users import CustomerRepository, UserRepository
from schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from schemas.user import UserRead


class AuthService:
    """Coordinate registration and login workflows."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize service dependencies."""
        self.db = db
        self.settings = get_settings()
        self.users = UserRepository(db)
        self.customers = CustomerRepository(db)

    async def register(self, data: RegisterRequest) -> TokenResponse:
        """Create a customer account and return an access token."""
        email = data.email.lower().strip()
        if await self.users.get_by_email(email):
            raise ConflictError("An account with that email already exists.")

        user = await self.users.create(
            {
                "email": email,
                "hashed_password": PasswordUtils.hash_password(data.password),
                "role": UserRole.CUSTOMER,
            }
        )
        await self.customers.create_profile(
            user_id=user.id,
            full_name=data.full_name,
            phone=data.phone,
        )
        return self.build_token_response(user)

    async def login(self, data: LoginRequest) -> TokenResponse:
        """Validate credentials and return an access token.

        A missing account and a wrong password produce the same error so
        the endpoint cannot be used to enumerate registered emails. The
        hash is verified even when no user matched, which keeps the
        response time from leaking existence either.
        """
        user = await self.users.get_by_email(data.email)
        stored_hash = (
            user.hashed_password if user else PasswordUtils.dummy_hash()
        )
        password_ok = PasswordUtils.verify_password(
            data.password,
            stored_hash,
        )

        if user is None or not password_ok:
            raise AuthenticationError("Invalid email or password.")
        if not user.is_active:
            raise AuthenticationError("This account has been disabled.")

        return self.build_token_response(user)

    def build_token_response(self, user: User) -> TokenResponse:
        """Build a signed token response for a user."""
        expires_in = self.settings.jwt_access_token_expire_minutes * 60
        token = create_access_token(
            subject=user.id,
            additional_claims={"email": user.email, "role": user.role.value},
        )
        return TokenResponse(
            access_token=token,
            expires_in=expires_in,
            user=UserRead.model_validate(user),
        )
