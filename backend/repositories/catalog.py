"""Repositories for services and appointment extras."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.service import ProductExtra, Service
from repositories.base import BaseRepository


class ServiceRepository(BaseRepository[Service]):
    """Data access for bookable services."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize repository for the Service model."""
        super().__init__(db, Service)

    async def list_services(
        self,
        *,
        active_only: bool = True,
    ) -> list[Service]:
        """Return services ordered by name."""
        statement = select(Service).order_by(Service.name)
        if active_only:
            statement = statement.where(Service.is_active.is_(True))
        result = await self.db.execute(statement)
        return list(result.scalars().all())

    async def count_active(self) -> int:
        """Return how many services are currently bookable."""
        statement = select(Service).where(Service.is_active.is_(True))
        result = await self.db.execute(statement)
        return len(result.scalars().all())

    async def get_active(self, service_id: str) -> Service | None:
        """Return a service only when it is bookable."""
        statement = (
            select(Service)
            .where(Service.id == service_id)
            .where(Service.is_active.is_(True))
        )
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def name_exists(
        self,
        name: str,
        *,
        exclude_id: str | None = None,
    ) -> bool:
        """Return True when another service already uses the name."""
        statement = select(Service.id).where(
            Service.name.ilike(name.strip())
        )
        if exclude_id:
            statement = statement.where(Service.id != exclude_id)
        result = await self.db.execute(statement)
        return result.first() is not None


class ProductExtraRepository(BaseRepository[ProductExtra]):
    """Data access for product extras."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize repository for the ProductExtra model."""
        super().__init__(db, ProductExtra)

    async def list_extras(
        self,
        *,
        active_only: bool = True,
    ) -> list[ProductExtra]:
        """Return extras ordered by name."""
        statement = select(ProductExtra).order_by(ProductExtra.name)
        if active_only:
            statement = statement.where(ProductExtra.is_active.is_(True))
        result = await self.db.execute(statement)
        return list(result.scalars().all())

    async def list_active_by_ids(
        self,
        extra_ids: list[str],
    ) -> list[ProductExtra]:
        """Return the active extras matching the requested ids."""
        if not extra_ids:
            return []
        statement = (
            select(ProductExtra)
            .where(ProductExtra.id.in_(extra_ids))
            .where(ProductExtra.is_active.is_(True))
            .order_by(ProductExtra.name)
        )
        result = await self.db.execute(statement)
        return list(result.scalars().all())

    async def name_exists(
        self,
        name: str,
        *,
        exclude_id: str | None = None,
    ) -> bool:
        """Return True when another extra already uses the name."""
        statement = select(ProductExtra.id).where(
            ProductExtra.name.ilike(name.strip())
        )
        if exclude_id:
            statement = statement.where(ProductExtra.id != exclude_id)
        result = await self.db.execute(statement)
        return result.first() is not None
