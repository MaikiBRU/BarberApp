"""Populate a fresh demo sandbox with a believable barbershop.

A visitor should land on a product, not on an empty form. Each sandbox
gets its own staff, catalog, opening hours and a handful of appointments
spread across the past, today and the coming days, so the dashboards and
the agenda show real numbers computed from real rows.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from auth.password_utils import PasswordUtils
from core.config import get_settings
from core.tenancy import Tenant
from models.appointment import Appointment
from models.demo import DemoSession
from models.enums import AppointmentStatus, PaymentMethod, UserRole
from repositories.catalog import ProductExtraRepository, ServiceRepository
from repositories.schedule import BusinessHoursRepository
from repositories.users import (
    BarberRepository,
    CustomerRepository,
    UserRepository,
)
from services.schedule_service import default_business_hours

SERVICES = (
    ("Corte clásico", "Corte a máquina y tijera con acabado", 45, 1300000),
    ("Corte + barba", "Corte completo con perfilado de barba", 60, 1700000),
    ("Perfilado de barba", "Diseño y afeitado con toalla caliente", 30, 900000),
    ("Corte infantil", "Corte para menores de 12 años", 30, 1000000),
)

EXTRAS = (
    ("Lavado", "Lavado y masaje capilar previo al servicio", 15, 300000),
    ("Mascarilla facial", "Tratamiento facial rápido", 15, 450000),
)

BARBERS = (
    ("Tomás Rivas", "Especialista en fades y cortes clásicos."),
    ("Lucía Ferrer", "Color, barbería moderna y trabajos de tijera."),
)

CUSTOMERS = (
    ("Martín Alonso", "+54 11 5555 0101"),
    ("Sofía Duarte", "+54 11 5555 0102"),
    ("Ignacio Pérez", "+54 11 5555 0103"),
)

#: The persona the visitor starts as, and the ones they can switch to.
VISITOR_NAME = "Vos (visitante)"


@dataclass(frozen=True, slots=True)
class SeededPersonas:
    """User ids for each role the visitor can step into."""

    admin_id: str
    barber_id: str
    customer_id: str


def _email(role: str, session_id: str, index: int = 0) -> str:
    """Return a globally unique address for a sandbox account.

    Emails are unique across the whole table, so every sandbox needs its
    own namespace; the visitor never sees these.
    """
    suffix = session_id[:10].lower().replace("_", "").replace("-", "")
    slot = f"{index}" if index else ""
    return f"{role}{slot}@{suffix}.demo.barberapp"


async def seed_sandbox(
    db: AsyncSession,
    session: DemoSession,
) -> SeededPersonas:
    """Fill an empty sandbox and return the personas it exposes."""
    tenant = Tenant.demo(session.id)
    users = UserRepository(db, tenant)
    barbers = BarberRepository(db, tenant)
    customers = CustomerRepository(db, tenant)

    # Nobody signs in to these with a password: the demo mints tokens
    # directly, so the stored hash is of an unguessable random value.
    password_hash = PasswordUtils.hash_password(session.id)

    admin = await users.create(
        {
            "email": _email("admin", session.id),
            "hashed_password": password_hash,
            "role": UserRole.ADMIN,
        }
    )

    barber_users = []
    for index, (name, bio) in enumerate(BARBERS, start=1):
        account = await users.create(
            {
                "email": _email("barbero", session.id, index),
                "hashed_password": password_hash,
                "role": UserRole.BARBER,
            }
        )
        await barbers.create_profile(
            user_id=account.id,
            display_name=name,
            bio=bio,
            phone=f"+54 11 5555 02{index:02d}",
        )
        barber_users.append(account)

    visitor = await users.create(
        {
            "email": _email("cliente", session.id),
            "hashed_password": password_hash,
            "role": UserRole.CUSTOMER,
        }
    )
    await customers.create_profile(
        user_id=visitor.id,
        full_name=VISITOR_NAME,
        phone="+54 11 5555 0100",
    )

    other_customers = []
    for index, (name, phone) in enumerate(CUSTOMERS, start=1):
        account = await users.create(
            {
                "email": _email("invitado", session.id, index),
                "hashed_password": password_hash,
                "role": UserRole.CUSTOMER,
            }
        )
        await customers.create_profile(
            user_id=account.id,
            full_name=name,
            phone=phone,
        )
        other_customers.append(account)

    catalog = await _seed_catalog(db, tenant)
    await _seed_hours(db, tenant)
    await _seed_appointments(
        db,
        tenant=tenant,
        barbers=barber_users,
        customers=other_customers,
        services=catalog,
    )

    return SeededPersonas(
        admin_id=admin.id,
        barber_id=barber_users[0].id,
        customer_id=visitor.id,
    )


async def _seed_catalog(db: AsyncSession, tenant: Tenant) -> list:
    """Create the sandbox catalog and return its services."""
    services = ServiceRepository(db, tenant)
    extras = ProductExtraRepository(db, tenant)

    created = []
    for name, description, minutes, price in SERVICES:
        created.append(
            await services.create(
                {
                    "name": name,
                    "description": description,
                    "duration_minutes": minutes,
                    "price_cents": price,
                }
            )
        )

    for name, description, minutes, price in EXTRAS:
        await extras.create(
            {
                "name": name,
                "description": description,
                "duration_minutes": minutes,
                "price_cents": price,
            }
        )

    return created


async def _seed_hours(db: AsyncSession, tenant: Tenant) -> None:
    """Copy the default weekly schedule into the sandbox."""
    hours = BusinessHoursRepository(db, tenant)
    for row in default_business_hours():
        await hours.create(
            {
                "weekday": row.weekday,
                "opens_at": row.opens_at,
                "closes_at": row.closes_at,
                "is_closed": row.is_closed,
            }
        )


def _at(day_offset: int, hour: int, minute: int = 0) -> datetime:
    """Return a shop-local wall clock time as a UTC instant."""
    timezone = get_settings().timezone
    local_day = (datetime.now(timezone) + timedelta(days=day_offset)).date()
    local = datetime.combine(
        local_day,
        datetime.min.time().replace(hour=hour, minute=minute),
        tzinfo=timezone,
    )
    return local.astimezone(UTC)


async def _seed_appointments(
    db: AsyncSession,
    *,
    tenant: Tenant,
    barbers: list,
    customers: list,
    services: list,
) -> None:
    """Create a spread of appointments so the dashboards are not empty.

    Times are written straight to the model rather than through the
    booking service: the seed intentionally places rows in the past,
    which the booking rules correctly refuse.
    """
    plan = (
        # (day offset, hour, barber, customer, service, status)
        (-2, 11, 0, 0, 0, AppointmentStatus.COMPLETED),
        (-2, 15, 1, 1, 1, AppointmentStatus.COMPLETED),
        (-1, 10, 0, 2, 3, AppointmentStatus.COMPLETED),
        (-1, 17, 1, 0, 2, AppointmentStatus.NO_SHOW),
        (0, 10, 0, 1, 0, AppointmentStatus.COMPLETED),
        (0, 12, 1, 2, 1, AppointmentStatus.CONFIRMED),
        (1, 11, 0, 0, 1, AppointmentStatus.CONFIRMED),
        (1, 16, 1, 1, 2, AppointmentStatus.PENDING),
        (2, 10, 0, 2, 0, AppointmentStatus.PENDING),
    )

    for entry in plan:
        offset, hour, barber_at, customer_at, service_at, status = entry
        service = services[service_at]
        starts_at = _at(offset, hour)
        db.add(
            Appointment(
                shop_id=tenant.shop_id,
                customer_id=customers[customer_at].id,
                barber_id=barbers[barber_at].id,
                service_id=service.id,
                starts_at=starts_at,
                ends_at=starts_at
                + timedelta(minutes=service.duration_minutes),
                duration_minutes=service.duration_minutes,
                status=status,
                service_price_cents=service.price_cents,
                extras_price_cents=0,
                payment_method=PaymentMethod.CASH,
                tip_cents=0,
            )
        )

    await db.flush()
