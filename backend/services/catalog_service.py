"""Catalog business logic for services and extras."""

from sqlalchemy.ext.asyncio import AsyncSession

from core.tenancy import Tenant
from exceptions.errors import ConflictError, NotFoundError
from repositories.catalog import ProductExtraRepository, ServiceRepository
from schemas.service import (
    ProductExtraCreate,
    ProductExtraRead,
    ProductExtraUpdate,
    ServiceCreate,
    ServiceRead,
    ServiceUpdate,
)


class CatalogService:
    """Coordinate service and extra workflows."""

    def __init__(
        self,
        db: AsyncSession,
        tenant: Tenant | None = None,
    ) -> None:
        """Wire the catalog repositories."""
        self.db = db
        self.tenant = tenant or Tenant.real()
        self.services = ServiceRepository(db, self.tenant)
        self.extras = ProductExtraRepository(db, self.tenant)

    async def list_services(
        self,
        *,
        include_inactive: bool = False,
    ) -> list[ServiceRead]:
        """Return services, optionally including deactivated ones."""
        rows = await self.services.list_services(
            active_only=not include_inactive
        )
        return [ServiceRead.model_validate(row) for row in rows]

    async def create_service(self, data: ServiceCreate) -> ServiceRead:
        """Create a bookable service."""
        if await self.services.name_exists(data.name):
            raise ConflictError("Ya existe un servicio con ese nombre.")
        service = await self.services.create(data.model_dump())
        return ServiceRead.model_validate(service)

    async def update_service(
        self,
        service_id: str,
        data: ServiceUpdate,
    ) -> ServiceRead:
        """Update a bookable service."""
        service = await self.services.get_by_id(service_id)
        if service is None:
            raise NotFoundError("service", service_id)

        changes = data.model_dump(exclude_unset=True)
        name = changes.get("name")
        if name and await self.services.name_exists(
            name,
            exclude_id=service_id,
        ):
            raise ConflictError("Ya existe un servicio con ese nombre.")

        updated = await self.services.update(service, changes)
        return ServiceRead.model_validate(updated)

    async def list_extras(
        self,
        *,
        include_inactive: bool = False,
    ) -> list[ProductExtraRead]:
        """Return extras, optionally including deactivated ones."""
        rows = await self.extras.list_extras(active_only=not include_inactive)
        return [ProductExtraRead.model_validate(row) for row in rows]

    async def create_extra(
        self,
        data: ProductExtraCreate,
    ) -> ProductExtraRead:
        """Create an appointment extra."""
        if await self.extras.name_exists(data.name):
            raise ConflictError("Ya existe un extra con ese nombre.")
        extra = await self.extras.create(data.model_dump())
        return ProductExtraRead.model_validate(extra)

    async def update_extra(
        self,
        extra_id: str,
        data: ProductExtraUpdate,
    ) -> ProductExtraRead:
        """Update an appointment extra."""
        extra = await self.extras.get_by_id(extra_id)
        if extra is None:
            raise NotFoundError("extra", extra_id)

        changes = data.model_dump(exclude_unset=True)
        name = changes.get("name")
        if name and await self.extras.name_exists(name, exclude_id=extra_id):
            raise ConflictError("Ya existe un extra con ese nombre.")

        updated = await self.extras.update(extra, changes)
        return ProductExtraRead.model_validate(updated)
