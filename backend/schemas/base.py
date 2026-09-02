"""Base schema helpers."""

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    """Base Pydantic schema with ORM attribute support."""

    model_config = ConfigDict(from_attributes=True)


class Page[ItemType](BaseModel):
    """A page of results plus the metadata a client needs to paginate."""

    items: list[ItemType]
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)

    @property
    def has_more(self) -> bool:
        """Return True when more rows exist after this page."""
        return self.offset + len(self.items) < self.total
