"""Centralized exception handling with a single error envelope.

Every error response has the shape::

    {"error": {"type": str, "message": str, "details": object | null}}

so the frontend only ever parses one contract.
"""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from core.config import get_settings
from exceptions.errors import AppError

logger = logging.getLogger(__name__)

STATUS_ERROR_TYPES: dict[int, str] = {
    400: "bad_request",
    401: "authentication_error",
    403: "authorization_error",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    422: "validation_error",
    429: "rate_limit_exceeded",
}


def error_response(
    status_code: int,
    error_type: str,
    message: str,
    *,
    details: Any = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """Build a JSON response using the shared error envelope."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "type": error_type,
                "message": message,
                "details": details,
            }
        },
        headers=headers,
    )


def _validation_details(exc: RequestValidationError) -> list[dict[str, Any]]:
    """Flatten Pydantic errors into a compact, serializable list."""
    details: list[dict[str, Any]] = []
    for error in exc.errors():
        location = [str(part) for part in error.get("loc", ())]
        field = ".".join(part for part in location if part != "body")
        details.append(
            {
                "field": field or "body",
                "message": error.get("msg", "Invalid value"),
                "type": error.get("type", "value_error"),
            }
        )
    return details


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the application."""
    settings = get_settings()

    @app.exception_handler(AppError)
    async def app_error_handler(
        request: Request,
        exc: AppError,
    ) -> JSONResponse:
        """Convert domain errors into the shared envelope."""
        headers: dict[str, str] | None = None
        if exc.status_code == 401:
            headers = {"WWW-Authenticate": "Bearer"}
        retry_after = getattr(exc, "retry_after", None)
        if retry_after:
            headers = {**(headers or {}), "Retry-After": str(retry_after)}

        return error_response(
            exc.status_code,
            exc.error_type,
            exc.message,
            details=exc.details or None,
            headers=headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """Return field-level validation details the UI can render."""
        return error_response(
            422,
            "validation_error",
            "Revisá los datos ingresados.",
            details=_validation_details(exc),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        """Normalize framework HTTP errors into the shared envelope."""
        error_type = STATUS_ERROR_TYPES.get(exc.status_code, "http_error")
        message = (
            exc.detail
            if isinstance(exc.detail, str)
            else "No se pudo completar la solicitud."
        )
        headers = dict(exc.headers) if exc.headers else None
        return error_response(
            exc.status_code,
            error_type,
            message,
            headers=headers,
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(
        request: Request,
        exc: IntegrityError,
    ) -> JSONResponse:
        """Surface database constraint violations as conflicts."""
        logger.warning(
            "Database integrity error on %s %s: %s",
            request.method,
            request.url.path,
            exc,
        )
        return error_response(
            409,
            "conflict",
            "La operación entra en conflicto con datos existentes.",
        )

    @app.exception_handler(SQLAlchemyError)
    async def database_error_handler(
        request: Request,
        exc: SQLAlchemyError,
    ) -> JSONResponse:
        """Log database failures without leaking SQL to clients."""
        logger.exception(
            "Database error on %s %s",
            request.method,
            request.url.path,
        )
        return error_response(
            503,
            "database_unavailable",
            "El servicio no está disponible en este momento.",
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Log unexpected failures and return a safe message."""
        logger.exception(
            "Unhandled error on %s %s",
            request.method,
            request.url.path,
        )
        details = {"exception": repr(exc)} if settings.debug else None
        return error_response(
            500,
            "internal_error",
            "Ocurrió un error inesperado.",
            details=details,
        )
