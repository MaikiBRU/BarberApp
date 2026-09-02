"""Seed local development data.

Development only. Against PostgreSQL run ``alembic upgrade head`` first;
``--create-tables`` is a convenience for the SQLite quick-start path.
"""

import argparse
import asyncio
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from auth.password_utils import PasswordUtils  # noqa: E402
from db.database import SessionLocal, create_all_tables  # noqa: E402
from models.enums import UserRole  # noqa: E402
from repositories.catalog import (  # noqa: E402
    ProductExtraRepository,
    ServiceRepository,
)
from repositories.schedule import BusinessHoursRepository  # noqa: E402
from repositories.users import (  # noqa: E402
    BarberRepository,
    CustomerRepository,
    UserRepository,
)
from services.schedule_service import default_business_hours  # noqa: E402

SERVICES = (
    ("Corte clasico", "Corte a maquina y tijera con acabado", 45, 1300000),
    ("Corte + barba", "Corte completo con perfilado de barba", 60, 1700000),
    ("Perfilado de barba", "Diseno y afeitado con toalla caliente", 30, 900000),
    ("Corte infantil", "Corte para menores de 12 anos", 30, 1000000),
)

EXTRAS = (
    ("Lavado", "Lavado y masaje capilar previo al servicio", 10, 300000),
    ("Mascarilla facial", "Tratamiento facial rapido", 15, 450000),
)

STAFF = (
    ("tomas@example.com", "Tomas Rivas", UserRole.BARBER),
    ("lucia@example.com", "Lucia Ferrer", UserRole.BARBER),
)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--create-tables",
        action="store_true",
        help="Create tables before seeding. SQLite quick-start only.",
    )
    parser.add_argument("--password", default="Password123!")
    return parser.parse_args()


async def ensure_user(session, *, email, password, role, name):
    """Create a user and its role profile when it does not exist."""
    users = UserRepository(session)
    existing = await users.get_by_email(email)
    if existing:
        return existing

    user = await users.create(
        {
            "email": email,
            "hashed_password": PasswordUtils.hash_password(password),
            "role": role,
        }
    )
    if role == UserRole.BARBER:
        await BarberRepository(session).create_profile(
            user_id=user.id,
            display_name=name,
            bio=f"{name} en BarberApp.",
        )
    elif role == UserRole.CUSTOMER:
        await CustomerRepository(session).create_profile(
            user_id=user.id,
            full_name=name,
        )
    return user


async def ensure_catalog(session) -> None:
    """Create the baseline catalog when it is empty."""
    services = ServiceRepository(session)
    if not await services.list_services(active_only=False):
        for name, description, minutes, price in SERVICES:
            await services.create(
                {
                    "name": name,
                    "description": description,
                    "duration_minutes": minutes,
                    "price_cents": price,
                }
            )

    extras = ProductExtraRepository(session)
    if not await extras.list_extras(active_only=False):
        for name, description, minutes, price in EXTRAS:
            await extras.create(
                {
                    "name": name,
                    "description": description,
                    "duration_minutes": minutes,
                    "price_cents": price,
                }
            )


async def ensure_business_hours(session) -> None:
    """Create the weekly opening schedule when it is empty."""
    hours = BusinessHoursRepository(session)
    if await hours.list_week():
        return
    for row in default_business_hours():
        session.add(row)
    await session.flush()


async def main() -> None:
    """Run development initialization."""
    args = parse_args()
    if args.create_tables:
        await create_all_tables()

    async with SessionLocal() as session:
        await ensure_user(
            session,
            email="admin@example.com",
            password=args.password,
            role=UserRole.ADMIN,
            name="Admin",
        )
        for email, name, role in STAFF:
            await ensure_user(
                session,
                email=email,
                password=args.password,
                role=role,
                name=name,
            )
        await ensure_user(
            session,
            email="cliente@example.com",
            password=args.password,
            role=UserRole.CUSTOMER,
            name="Cliente Demo",
        )
        await ensure_catalog(session)
        await ensure_business_hours(session)
        await session.commit()

    print("Development data ready.")
    print(f"  admin@example.com    / {args.password}  (admin)")
    print(f"  tomas@example.com    / {args.password}  (barber)")
    print(f"  lucia@example.com    / {args.password}  (barber)")
    print(f"  cliente@example.com  / {args.password}  (customer)")


if __name__ == "__main__":
    asyncio.run(main())
