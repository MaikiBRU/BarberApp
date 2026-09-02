"""Service catalog routes."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.jwt_config import require_role
from db.session import get_db
from models.enums import UserRole
from models.user import User
from schemas.service import (
    ProductExtraCreate,
    ProductExtraRead,
    ProductExtraUpdate,
    ServiceCreate,
    ServiceRead,
    ServiceUpdate,
)
from services.catalog_service import CatalogService

router = APIRouter(prefix="/catalog", tags=["catalog"])

require_admin = require_role(UserRole.ADMIN)


@router.get(
    "/services",
    response_model=list[ServiceRead],
    summary="List bookable services",
)
async def list_services(
    db: AsyncSession = Depends(get_db),
) -> list[ServiceRead]:
    """Return the services customers can book."""
    return await CatalogService(db).list_services()


@router.get(
    "/admin/services",
    response_model=list[ServiceRead],
    summary="List every service, including deactivated ones",
)
async def list_services_admin(
    include_inactive: bool = Query(default=True),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[ServiceRead]:
    """Return every service for the admin catalog screen."""
    return await CatalogService(db).list_services(
        include_inactive=include_inactive,
    )


@router.post(
    "/services",
    response_model=ServiceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a service",
)
async def create_service(
    payload: ServiceCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> ServiceRead:
    """Create a bookable service. Administrators only."""
    return await CatalogService(db).create_service(payload)


@router.patch(
    "/services/{service_id}",
    response_model=ServiceRead,
    summary="Update a service",
)
async def update_service(
    service_id: str,
    payload: ServiceUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> ServiceRead:
    """Update a service. Administrators only."""
    return await CatalogService(db).update_service(service_id, payload)


@router.get(
    "/extras",
    response_model=list[ProductExtraRead],
    summary="List bookable extras",
)
async def list_extras(
    db: AsyncSession = Depends(get_db),
) -> list[ProductExtraRead]:
    """Return the add-ons customers can attach to a booking."""
    return await CatalogService(db).list_extras()


@router.get(
    "/admin/extras",
    response_model=list[ProductExtraRead],
    summary="List every extra, including deactivated ones",
)
async def list_extras_admin(
    include_inactive: bool = Query(default=True),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[ProductExtraRead]:
    """Return every extra for the admin catalog screen."""
    return await CatalogService(db).list_extras(
        include_inactive=include_inactive,
    )


@router.post(
    "/extras",
    response_model=ProductExtraRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an extra",
)
async def create_extra(
    payload: ProductExtraCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> ProductExtraRead:
    """Create an appointment extra. Administrators only."""
    return await CatalogService(db).create_extra(payload)


@router.patch(
    "/extras/{extra_id}",
    response_model=ProductExtraRead,
    summary="Update an extra",
)
async def update_extra(
    extra_id: str,
    payload: ProductExtraUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> ProductExtraRead:
    """Update an appointment extra. Administrators only."""
    return await CatalogService(db).update_extra(extra_id, payload)
