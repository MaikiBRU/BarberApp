"""Domain enums used by database models and schemas."""

from enum import IntEnum, StrEnum


class UserRole(StrEnum):
    """Supported application roles."""

    ADMIN = "admin"
    BARBER = "barber"
    CUSTOMER = "customer"


class AppointmentStatus(StrEnum):
    """Lifecycle states for an appointment."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class PaymentMethod(StrEnum):
    """Supported payment methods."""

    CASH = "cash"
    TRANSFER = "transfer"
    CARD = "card"
    MERCADO_PAGO = "mercado_pago"


class PaymentStatus(StrEnum):
    """Payment lifecycle states."""

    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class Weekday(IntEnum):
    """Days of the week matching ``datetime.weekday()``."""

    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


#: Appointment states that still occupy a slot in the barber's agenda.
BLOCKING_STATUSES: frozenset[AppointmentStatus] = frozenset(
    {AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED}
)

#: States from which no further transition is allowed.
TERMINAL_STATUSES: frozenset[AppointmentStatus] = frozenset(
    {
        AppointmentStatus.CANCELLED,
        AppointmentStatus.COMPLETED,
        AppointmentStatus.NO_SHOW,
    }
)

#: Allowed appointment state machine transitions.
STATUS_TRANSITIONS: dict[AppointmentStatus, frozenset[AppointmentStatus]] = {
    AppointmentStatus.PENDING: frozenset(
        {
            AppointmentStatus.CONFIRMED,
            AppointmentStatus.CANCELLED,
            AppointmentStatus.NO_SHOW,
            AppointmentStatus.COMPLETED,
        }
    ),
    AppointmentStatus.CONFIRMED: frozenset(
        {
            AppointmentStatus.COMPLETED,
            AppointmentStatus.CANCELLED,
            AppointmentStatus.NO_SHOW,
        }
    ),
    AppointmentStatus.CANCELLED: frozenset(),
    AppointmentStatus.COMPLETED: frozenset(),
    AppointmentStatus.NO_SHOW: frozenset(),
}


def enum_values(enum_class: type[StrEnum]) -> list[str]:
    """Return enum values so the database stores values, not names."""
    return [item.value for item in enum_class]
