"""API v1 router aggregation."""

import logging

from fastapi import APIRouter

from api.v1.routes import (
    appointments_router,
    auth_router,
    catalog_router,
    dashboard_router,
    schedule_router,
    users_router,
)
from db.database import check_database_connection
from exceptions.errors import AppError

logger = logging.getLogger(__name__)

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(catalog_router)
api_router.include_router(schedule_router)
api_router.include_router(users_router)
api_router.include_router(appointments_router)
api_router.include_router(dashboard_router)


class DatabaseUnavailable(AppError):
    """The API is up but cannot reach its database."""

    status_code = 503
    error_type = "database_unavailable"


@api_router.get("/health", tags=["health"], summary="Liveness probe")
async def api_health_check() -> dict[str, str]:
    """Return versioned API health status."""
    return {"status": "healthy"}


@api_router.get("/ready", tags=["health"], summary="Readiness probe")
async def readiness_check() -> dict[str, str]:
    """Return API and database readiness."""
    try:
        await check_database_connection()
    except Exception as exc:
        logger.warning("Readiness check failed: %s", exc)
        raise DatabaseUnavailable(
            "The database is not reachable.",
        ) from exc
    return {"status": "ready", "database": "connected"}
