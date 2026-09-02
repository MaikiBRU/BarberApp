"""User, barber and customer profile data access."""

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.tenancy import Tenant, scope
from models.user import BarberProfile, CustomerProfile, User
from repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Data access for users and their role profiles."""

    def __init__(self, db: AsyncSession, tenant: Tenant | None = None) -> None:
        """Initialize repository for the User model."""
        super().__init__(db, User, tenant, User.shop_id)

    async def get_by_email(self, email: str) -> User | None:
        """Return a user of this tenant by normalized email."""
        statement = self.scoped(
            select(User).where(User.email == email.lower().strip())
        )
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def get_with_profiles(self, user_id: str) -> User | None:
        """Return a user with both role profiles eagerly loaded."""
        statement = self.scoped(
            select(User)
            .options(
                selectinload(User.barber_profile),
                selectinload(User.customer_profile),
            )
            .where(User.id == user_id)
        )
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def count_active_barbers(self) -> int:
        """Return how many barbers can currently take appointments."""
        statement = scope(
            select(func.count())
            .select_from(BarberProfile)
            .join(User, User.id == BarberProfile.user_id)
            .where(BarberProfile.is_active.is_(True))
            .where(User.is_active.is_(True)),
            User.shop_id,
            self.tenant,
        )
        result = await self.db.execute(statement)
        return int(result.scalar_one())


class BarberRepository(BaseRepository[BarberProfile]):
    """Data access for barber profiles.

    Barber profiles have no ``shop_id`` of their own: they inherit the
    tenant of the account that owns them, so every query joins ``users``.
    """

    def __init__(self, db: AsyncSession, tenant: Tenant | None = None) -> None:
        """Initialize repository for the BarberProfile model."""
        super().__init__(db, BarberProfile, tenant)

    def _base_query(self) -> Select:
        """Return the shared barber query, scoped and eagerly loaded."""
        return scope(
            select(BarberProfile)
            .options(selectinload(BarberProfile.user))
            .join(User, User.id == BarberProfile.user_id)
            .order_by(BarberProfile.display_name),
            User.shop_id,
            self.tenant,
        )

    async def list_barbers(
        self,
        *,
        active_only: bool = True,
    ) -> list[BarberProfile]:
        """Return barber profiles, optionally only bookable ones."""
        statement = self._base_query()
        if active_only:
            statement = statement.where(
                BarberProfile.is_active.is_(True)
            ).where(User.is_active.is_(True))
        result = await self.db.execute(statement)
        return list(result.scalars().all())

    async def get_by_id(self, identifier: str) -> BarberProfile | None:
        """Return a barber profile owned by the tenant."""
        return await self.get_profile(identifier)

    async def get_profile(self, barber_id: str) -> BarberProfile | None:
        """Return one barber profile with its user loaded."""
        statement = self._base_query().where(BarberProfile.id == barber_id)
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: str) -> BarberProfile | None:
        """Return the barber profile owned by a user account."""
        statement = self._base_query().where(BarberProfile.user_id == user_id)
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def create_profile(
        self,
        *,
        user_id: str,
        display_name: str,
        bio: str | None = None,
        phone: str | None = None,
    ) -> BarberProfile:
        """Create a barber profile for an existing user."""
        profile = BarberProfile(
            user_id=user_id,
            display_name=display_name,
            bio=bio,
            phone=phone,
        )
        self.db.add(profile)
        await self.db.flush()
        await self.db.refresh(profile)
        return profile


class CustomerRepository(BaseRepository[CustomerProfile]):
    """Data access for customer profiles."""

    def __init__(self, db: AsyncSession, tenant: Tenant | None = None) -> None:
        """Initialize repository for the CustomerProfile model."""
        super().__init__(db, CustomerProfile, tenant)

    async def get_by_user_id(self, user_id: str) -> CustomerProfile | None:
        """Return the customer profile owned by a user of this tenant."""
        statement = scope(
            select(CustomerProfile)
            .join(User, User.id == CustomerProfile.user_id)
            .where(CustomerProfile.user_id == user_id),
            User.shop_id,
            self.tenant,
        )
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def create_profile(
        self,
        *,
        user_id: str,
        full_name: str | None = None,
        phone: str | None = None,
    ) -> CustomerProfile:
        """Create a customer profile for an existing user."""
        profile = CustomerProfile(
            user_id=user_id,
            full_name=full_name,
            phone=phone,
        )
        self.db.add(profile)
        await self.db.flush()
        await self.db.refresh(profile)
        return profile
