"""Create an internal user account from the command line.

Public registration only creates customers. Admin and barber accounts
are created here or through the admin-only API endpoints.
"""

import argparse
import asyncio
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from auth.password_utils import PasswordUtils  # noqa: E402
from db.database import SessionLocal  # noqa: E402
from models.enums import UserRole  # noqa: E402
from repositories.users import (  # noqa: E402
    BarberRepository,
    CustomerRepository,
    UserRepository,
)

MIN_PASSWORD_LENGTH = 8


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument(
        "--role",
        choices=[role.value for role in UserRole],
        default=UserRole.ADMIN.value,
    )
    parser.add_argument("--full-name", default=None)
    return parser.parse_args()


async def create_user(args: argparse.Namespace) -> None:
    """Create a user and the matching role profile."""
    if len(args.password) < MIN_PASSWORD_LENGTH:
        raise SystemExit(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters.",
        )

    role = UserRole(args.role)
    email = args.email.lower().strip()

    async with SessionLocal() as session:
        users = UserRepository(session)
        if await users.get_by_email(email):
            raise SystemExit(f"User already exists: {email}")

        user = await users.create(
            {
                "email": email,
                "hashed_password": PasswordUtils.hash_password(args.password),
                "role": role,
            }
        )
        if role == UserRole.CUSTOMER:
            await CustomerRepository(session).create_profile(
                user_id=user.id,
                full_name=args.full_name,
            )
        elif role == UserRole.BARBER:
            await BarberRepository(session).create_profile(
                user_id=user.id,
                display_name=args.full_name or email,
            )
        await session.commit()

    print(f"Created {role.value} user: {email}")


if __name__ == "__main__":
    asyncio.run(create_user(parse_args()))
