"""Domain error types."""

from exceptions.errors import (
    AppError,
    AuthenticationError,
    AuthorizationError,
    BusinessRuleError,
    ConflictError,
    NotFoundError,
    RateLimitError,
    SlotUnavailableError,
    ValidationError,
)

__all__ = [
    "AppError",
    "AuthenticationError",
    "AuthorizationError",
    "BusinessRuleError",
    "ConflictError",
    "NotFoundError",
    "RateLimitError",
    "SlotUnavailableError",
    "ValidationError",
]
