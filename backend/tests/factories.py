"""Test data builders and API helpers."""

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from auth.password_utils import PasswordUtils
from core.config import get_settings
from models.enums import UserRole
from models.schedule import BusinessHours
from repositories.catalog import ProductExtraRepository, ServiceRepository
from repositories.users import (
    BarberRepository,
    CustomerRepository,
    UserRepository,
)

TEST_PASSWORD = "Password123!"

#: Open every day 09:00-19:00 local time, so tests never depend on the
#: weekday the suite happens to run on.
OPEN_FROM = time(9, 0)
OPEN_TO = time(19, 0)


@dataclass(frozen=True)
class SeedIds:
    """Identifiers produced by the baseline seed."""

    admin_email: str = "admin@example.com"
    barber_email: str = "barber@example.com"
    second_barber_email: str = "barber2@example.com"
    customer_email: str = "customer@example.com"


SEED = SeedIds()


async def seed_baseline(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Create staff, catalog and opening hours used by API tests."""
    async with session_factory() as session:
        users = UserRepository(session)
        barbers = BarberRepository(session)
        customers = CustomerRepository(session)

        admin = await users.create(
            {
                "email": SEED.admin_email,
                "hashed_password": PasswordUtils.hash_password(TEST_PASSWORD),
                "role": UserRole.ADMIN,
            }
        )
        del admin

        for email, name in (
            (SEED.barber_email, "Tomas"),
            (SEED.second_barber_email, "Lucia"),
        ):
            barber = await users.create(
                {
                    "email": email,
                    "hashed_password": PasswordUtils.hash_password(
                        TEST_PASSWORD
                    ),
                    "role": UserRole.BARBER,
                }
            )
            await barbers.create_profile(
                user_id=barber.id,
                display_name=name,
            )

        customer = await users.create(
            {
                "email": SEED.customer_email,
                "hashed_password": PasswordUtils.hash_password(TEST_PASSWORD),
                "role": UserRole.CUSTOMER,
            }
        )
        await customers.create_profile(
            user_id=customer.id,
            full_name="Cliente Demo",
            phone="+54 11 5555 5555",
        )

        services = ServiceRepository(session)
        await services.create(
            {
                "name": "Corte clásico",
                "description": "Corte profesional",
                "duration_minutes": 45,
                "price_cents": 1300000,
            }
        )
        await services.create(
            {
                "name": "Corte largo",
                "duration_minutes": 90,
                "price_cents": 2000000,
            }
        )

        extras = ProductExtraRepository(session)
        await extras.create(
            {
                "name": "Lavado",
                "duration_minutes": 15,
                "price_cents": 300000,
            }
        )

        for weekday in range(7):
            session.add(
                BusinessHours(
                    weekday=weekday,
                    opens_at=OPEN_FROM,
                    closes_at=OPEN_TO,
                    is_closed=False,
                )
            )

        await session.commit()


def next_business_day(days_ahead: int = 2) -> date:
    """Return a local shop date safely inside the booking horizon."""
    settings = get_settings()
    local_now = datetime.now(settings.timezone)
    return (local_now + timedelta(days=days_ahead)).date()


class ApiHelper:
    """Thin wrapper that keeps API tests readable."""

    def __init__(self, client: TestClient) -> None:
        """Store the test client."""
        self.client = client

    def login(self, email: str, password: str = TEST_PASSWORD) -> str:
        """Return an access token for an existing account."""
        response = self.client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert response.status_code == 200, response.text
        return response.json()["access_token"]

    def auth(self, email: str) -> dict[str, str]:
        """Return an Authorization header for an existing account."""
        return {"Authorization": f"Bearer {self.login(email)}"}

    def register(
        self,
        email: str,
        full_name: str = "Nuevo Cliente",
    ) -> dict[str, Any]:
        """Register a customer and return the token payload."""
        response = self.client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": TEST_PASSWORD,
                "full_name": full_name,
            },
        )
        assert response.status_code == 201, response.text
        return response.json()

    def service_id(self, name: str = "Corte clásico") -> str:
        """Return the id of a seeded service by name."""
        services = self.client.get("/api/v1/catalog/services").json()
        return next(item["id"] for item in services if item["name"] == name)

    def extra_id(self, name: str = "Lavado") -> str:
        """Return the id of a seeded extra by name."""
        extras = self.client.get("/api/v1/catalog/extras").json()
        return next(item["id"] for item in extras if item["name"] == name)

    def barbers(self) -> list[dict[str, Any]]:
        """Return the public barber list."""
        return self.client.get("/api/v1/users/barbers").json()

    def barber(self, display_name: str = "Tomas") -> dict[str, Any]:
        """Return one seeded barber by display name."""
        return next(
            item
            for item in self.barbers()
            if item["display_name"] == display_name
        )

    def availability(
        self,
        *,
        service_id: str,
        day: date,
        barber_id: str | None = None,
        extra_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Return the availability payload for one day."""
        params: list[tuple[str, str]] = [
            ("service_id", service_id),
            ("date", day.isoformat()),
        ]
        if barber_id:
            params.append(("barber_id", barber_id))
        for extra in extra_ids or []:
            params.append(("extra_ids", extra))

        response = self.client.get(
            "/api/v1/appointments/availability",
            params=params,
        )
        assert response.status_code == 200, response.text
        return response.json()

    def first_slot(
        self,
        *,
        service_id: str,
        day: date,
        barber_id: str,
        extra_ids: list[str] | None = None,
    ) -> str:
        """Return the first bookable start time for a barber."""
        payload = self.availability(
            service_id=service_id,
            day=day,
            barber_id=barber_id,
            extra_ids=extra_ids,
        )
        slots = payload["barbers"][0]["slots"]
        assert slots, "expected at least one available slot"
        return slots[0]["starts_at"]


def utc_now() -> datetime:
    """Return the current instant in UTC."""
    return datetime.now(UTC)
