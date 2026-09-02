"""FastAPI application entry point."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1.routers import api_router
from core.config import get_settings
from core.logging_config import setup_logging
from db.database import check_database_connection
from middleware.exception_handler import register_exception_handlers
from middleware.rate_limit import RateLimitMiddleware
from middleware.request_context import RequestContextMiddleware

settings = get_settings()
setup_logging()
logger = logging.getLogger(__name__)

API_DESCRIPTION = """
Booking and operations API for a single barbershop.

**Roles**

* `customer` books and manages their own appointments.
* `barber` works their own agenda.
* `admin` manages the catalog, the staff and every appointment.

Availability is always computed by the server. Clients render the slots
this API returns and the booking endpoint revalidates the chosen slot
before writing, so a stale or forged slot cannot create a double booking.
""".strip()


def _assert_production_ready() -> None:
    """Refuse to boot a production process with unsafe configuration."""
    errors = settings.production_config_errors()
    if errors:
        for error in errors:
            logger.critical("Unsafe production configuration: %s", error)
        raise RuntimeError(
            "Refusing to start in production: " + "; ".join(errors)
        )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Run startup and shutdown hooks."""
    _assert_production_ready()
    logger.info(
        "Starting %s v%s (%s)",
        settings.app_name,
        settings.version,
        settings.app_env,
    )

    try:
        await check_database_connection()
        logger.info("Database connection successful")
    except Exception as exc:
        logger.warning("Database connection unavailable: %s", exc)

    yield

    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    description=API_DESCRIPTION,
    version=settings.version,
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
    openapi_url="/api/openapi.json" if settings.debug else None,
    lifespan=lifespan,
)

app.add_middleware(RequestContextMiddleware)
if settings.rate_limit_enabled:
    app.add_middleware(
        RateLimitMiddleware,
        max_requests=settings.rate_limit_auth_max_requests,
        window_seconds=settings.rate_limit_auth_window_seconds,
    )
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)

register_exception_handlers(app)
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["health"], summary="API metadata")
async def root() -> dict[str, str]:
    """Return API metadata."""
    return {
        "app": settings.app_name,
        "version": settings.version,
        "docs": "/api/docs" if settings.debug else "disabled",
    }


@app.get("/health", tags=["health"], summary="Liveness probe")
async def health_check() -> dict[str, str]:
    """Return a liveness signal that does not touch the database."""
    return {"status": "healthy", "app": settings.app_name}
