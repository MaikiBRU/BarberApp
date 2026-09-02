"""Staff and customer profile business logic."""

from sqlalchemy.ext.asyncio import AsyncSession

from auth.password_utils import PasswordUtils
from exceptions.errors import ConflictError, NotFoundError
from models.enums import UserRole
from models.user import BarberProfile, User
from repositories.users import (
    BarberRepository,
    CustomerRepository,
    UserRepository,
)
from schemas.user import (
    BarberCreate,
    BarberRead,
    BarberUpdate,
    CustomerProfileRead,
    CustomerProfileUpdate,
)


class UserService:
    """Coordinate barber management and customer profiles."""

    def __init__(self, db: AsyncSession) -> None:
        """Wire the user repositories."""
        self.db = db
        self.users = UserRepository(db)
        self.barbers = BarberRepository(db)
        self.customers = CustomerRepository(db)

    # ------------------------------------------------------------------
    # Barbers
    # ------------------------------------------------------------------
    async def list_barbers(
        self,
        *,
        include_inactive: bool = False,
        include_contact: bool = False,
    ) -> list[BarberRead]:
        """Return barber profiles for booking or administration."""
        rows = await self.barbers.list_barbers(
            active_only=not include_inactive
        )
        return [self._to_barber_read(row, include_contact) for row in rows]

    async def create_barber(self, data: BarberCreate) -> BarberRead:
        """Create a barber account together with its profile."""
        email = data.email.lower().strip()
        if await self.users.get_by_email(email):
            raise ConflictError("An account with that email already exists.")

        user = await self.users.create(
            {
                "email": email,
                "hashed_password": PasswordUtils.hash_password(data.password),
                "role": UserRole.BARBER,
            }
        )
        profile = await self.barbers.create_profile(
            user_id=user.id,
            display_name=data.display_name,
            bio=data.bio,
            phone=data.phone,
        )
        profile.user = user
        return self._to_barber_read(profile, include_contact=True)

    async def update_barber(
        self,
        barber_id: str,
        data: BarberUpdate,
    ) -> BarberRead:
        """Update a barber profile."""
        profile = await self.barbers.get_profile(barber_id)
        if profile is None:
            raise NotFoundError("Barber", barber_id)

        updated = await self.barbers.update(
            profile,
            data.model_dump(exclude_unset=True),
        )
        return self._to_barber_read(updated, include_contact=True)

    async def get_barber_profile_for_user(
        self,
        user: User,
    ) -> BarberProfile:
        """Return the barber profile owned by a user account."""
        profile = await self.barbers.get_by_user_id(user.id)
        if profile is None:
            raise NotFoundError("Barber profile", user.id)
        return profile

    # ------------------------------------------------------------------
    # Customers
    # ------------------------------------------------------------------
    async def get_customer_profile(self, user: User) -> CustomerProfileRead:
        """Return the profile of the authenticated customer."""
        profile = await self.customers.get_by_user_id(user.id)
        return CustomerProfileRead(
            user_id=user.id,
            email=user.email,
            full_name=profile.full_name if profile else None,
            phone=profile.phone if profile else None,
        )

    async def update_customer_profile(
        self,
        user: User,
        data: CustomerProfileUpdate,
    ) -> CustomerProfileRead:
        """Update the profile of the authenticated customer."""
        profile = await self.customers.get_by_user_id(user.id)
        changes = data.model_dump(exclude_unset=True)

        if profile is None:
            profile = await self.customers.create_profile(
                user_id=user.id,
                full_name=changes.get("full_name"),
                phone=changes.get("phone"),
            )
        elif changes:
            profile = await self.customers.update(profile, changes)

        return CustomerProfileRead(
            user_id=user.id,
            email=user.email,
            full_name=profile.full_name,
            phone=profile.phone,
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    @staticmethod
    def _to_barber_read(
        profile: BarberProfile,
        include_contact: bool,
    ) -> BarberRead:
        """Serialize a barber profile, hiding contact data by default."""
        return BarberRead(
            id=profile.id,
            user_id=profile.user_id,
            display_name=profile.display_name,
            bio=profile.bio,
            is_active=profile.is_active and profile.user.is_active,
            email=profile.user.email if include_contact else None,
            phone=profile.phone if include_contact else None,
        )
