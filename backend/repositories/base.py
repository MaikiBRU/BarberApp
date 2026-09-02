"""Base repository helpers for SQLAlchemy models."""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.base import Base


class BaseRepository[ModelType: Base]:
    """Small async repository wrapper around a SQLAlchemy model.

    Repositories own persistence concerns only. They never commit: the
    request-scoped session dependency owns the transaction boundary so a
    single request stays atomic across several repositories.
    """

    def __init__(self, db: AsyncSession, model: type[ModelType]) -> None:
        """Initialize repository with a session and model class."""
        self.db = db
        self.model = model

    async def get_by_id(self, identifier: str) -> ModelType | None:
        """Return a model by primary key."""
        return await self.db.get(self.model, identifier)

    async def list(self, limit: int = 100, offset: int = 0) -> list[ModelType]:
        """Return a paginated list of models."""
        statement = select(self.model).limit(limit).offset(offset)
        result = await self.db.execute(statement)
        return list(result.scalars().all())

    async def count(self) -> int:
        """Return the total number of rows for the model."""
        statement = select(func.count()).select_from(self.model)
        result = await self.db.execute(statement)
        return int(result.scalar_one())

    async def create(self, data: dict[str, Any]) -> ModelType:
        """Create and flush a model instance."""
        instance = self.model(**data)
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
