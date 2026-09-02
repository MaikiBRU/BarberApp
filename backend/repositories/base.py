"""Base repository helpers for SQLAlchemy models."""

from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.tenancy import Tenant, scope
from models.base import Base


class BaseRepository[ModelType: Base]:
    """Small async repository wrapper around a SQLAlchemy model.

    Repositories own persistence concerns only. They never commit: the
    request-scoped session dependency owns the transaction boundary so a
    single request stays atomic across several repositories.

    When ``tenant_column`` is given, every read is filtered by the active
    tenant and every write is stamped with it. That single rule is what
    keeps a demo sandbox from reaching the real shop's rows.
    """

    def __init__(
        self,
        db: AsyncSession,
        model: type[ModelType],
        tenant: Tenant | None = None,
        tenant_column: Any = None,
    ) -> None:
        """Initialize with a session, a model and the tenant in play."""
        self.db = db
        self.model = model
        self.tenant = tenant or Tenant.real()
        self.tenant_column = tenant_column

    # ------------------------------------------------------------------
    # Tenant plumbing
    # ------------------------------------------------------------------
    def scoped(self, statement: Select) -> Select:
        """Restrict a query to the active tenant when applicable."""
        if self.tenant_column is None:
            return statement
        return scope(statement, self.tenant_column, self.tenant)

    def owned(self, instance: ModelType | None) -> ModelType | None:
        """Return the instance only when the tenant owns it."""
        if instance is None or self.tenant_column is None:
            return instance
        return (
            instance
            if self.tenant.owns(getattr(instance, "shop_id", None))
            else None
        )

    def stamped(self, data: dict[str, Any]) -> dict[str, Any]:
        """Attach the tenant id to a payload about to be inserted."""
        if self.tenant_column is None:
            return data
        return {**data, "shop_id": self.tenant.shop_id}

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    async def get_by_id(self, identifier: str) -> ModelType | None:
        """Return a model by primary key, scoped to the tenant."""
        return self.owned(await self.db.get(self.model, identifier))

    async def list(self, limit: int = 100, offset: int = 0) -> list[ModelType]:
        """Return a paginated list of models."""
        statement = self.scoped(select(self.model)).limit(limit).offset(offset)
        result = await self.db.execute(statement)
        return list(result.scalars().all())

    async def count(self) -> int:
        """Return the number of rows visible to the tenant."""
        statement = self.scoped(select(func.count()).select_from(self.model))
        result = await self.db.execute(statement)
        return int(result.scalar_one())

    async def create(self, data: dict[str, Any]) -> ModelType:
        """Create and flush a model instance stamped with the tenant."""
        instance = self.model(**self.stamped(data))
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def update(
        self,
        instance: ModelType,
        data: dict[str, Any],
    ) -> ModelType:
        """Update and flush a model instance."""
        for key, value in data.items():
            setattr(instance, key, value)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def delete(self, instance: ModelType) -> None:
        """Delete a model instance."""
        await self.db.delete(instance)
        await self.db.flush()
