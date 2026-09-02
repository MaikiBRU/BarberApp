"""Versioned API route modules."""

from api.v1.routes.appointments import router as appointments_router
from api.v1.routes.auth import router as auth_router
from api.v1.routes.catalog import router as catalog_router
from api.v1.routes.dashboard import router as dashboard_router
from api.v1.routes.schedule import router as schedule_router
from api.v1.routes.users import router as users_router

__all__ = [
    "appointments_router",
    "auth_router",
    "catalog_router",
    "dashboard_router",
    "schedule_router",
    "users_router",
]
