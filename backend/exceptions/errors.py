"""Domain error hierarchy shared by services and API layers.

Services raise these instead of framework exceptions so business logic
stays independent from FastAPI. `middleware.exception_handler` converts
them into a single consistent HTTP error envelope.
"""

from typing import Any


class AppError(Exception):
    """Base application error carrying an HTTP status and a type slug."""

    status_code: int = 500
    error_type: str = "internal_error"

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Store the public message and optional structured details."""
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_payload(self) -> dict[str, Any]:
        """Return the serializable error envelope body."""
        return {
            "error": {
                "type": self.error_type,
                "message": self.message,
                "details": self.details or None,
            }
        }


class ValidationError(AppError):
    """Input failed domain validation."""

    status_code = 422
    error_type = "validation_error"


class AuthenticationError(AppError):
    """Credentials are missing or invalid."""

    status_code = 401
    error_type = "authentication_error"

    def __init__(
        self,
        message: str = "Tu sesión no es válida. Iniciá sesión de nuevo.",
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Default to a generic message that leaks no account state."""
        super().__init__(message, details=details)


class AuthorizationError(AppError):
    """Authenticated but not allowed to perform the action."""

    status_code = 403
    error_type = "authorization_error"

    def __init__(
        self,
        message: str = "Tu cuenta no tiene permiso para hacer esto.",
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Default to a generic forbidden message."""
        super().__init__(message, details=details)


#: Spanish sentence per resource slug. A template would get the
#: grammatical gender wrong half the time.
NOT_FOUND_MESSAGES: dict[str, str] = {
    "appointment": "El turno no existe o no está disponible.",
    "service": "El servicio no existe o ya no se ofrece.",
    "extra": "El extra no existe o ya no está disponible.",
    "barber": "El barbero no existe o no está tomando turnos.",
    "barber_profile": "No encontramos el perfil de barbero.",
    "customer": "El cliente no existe.",
    "time_off": "La ausencia no existe.",
}


class NotFoundError(AppError):
    """Requested resource does not exist or is not visible."""

    status_code = 404
    error_type = "not_found"

    def __init__(
        self,
        resource: str,
        identifier: str | None = None,
    ) -> None:
        """Build a message from the resource slug and optional id."""
        message = NOT_FOUND_MESSAGES.get(
            resource,
            "No encontramos lo que buscabas.",
        )
        details = {"resource": resource}
        if identifier:
            details["id"] = identifier
        super().__init__(message, details=details)


class ConflictError(AppError):
    """Request conflicts with the current state of the resource."""

    status_code = 409
    error_type = "conflict"


class SlotUnavailableError(ConflictError):
    """The requested appointment slot is already taken or invalid."""

    error_type = "slot_unavailable"

    def __init__(
        self,
        message: str = "Ese horario ya fue tomado. Elegí otro, por favor.",
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Default to the booking-conflict message."""
        super().__init__(message, details=details)


class BusinessRuleError(AppError):
    """A domain rule forbids the requested operation."""

    status_code = 422
    error_type = "business_rule_error"


class RateLimitError(AppError):
    """Too many requests from the same client."""

    status_code = 429
    error_type = "rate_limit_exceeded"

    def __init__(
        self,
        message: str = "Demasiados intentos. Probá de nuevo en unos minutos.",
        *,
        retry_after: int | None = None,
    ) -> None:
        """Attach the retry window when the caller knows it."""
        details = {"retry_after_seconds": retry_after} if retry_after else None
        super().__init__(message, details=details)
        self.retry_after = retry_after
