"""Remove expired demo sandboxes and everything they own.

Safe to run repeatedly and safe to run while the API is serving: it only
touches sessions that are already past their TTL or revoked, and every
row it deletes carries that session's id.

    python scripts/cleanup_demo.py
"""

import asyncio
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from db.database import SessionLocal  # noqa: E402
from services.demo_service import cleanup_expired  # noqa: E402


async def main() -> None:
    """Purge expired sandboxes and report how many were removed."""
    async with SessionLocal() as session:
        removed = await cleanup_expired(session)
        await session.commit()
    print(f"Removed {removed} expired demo sandbox(es).")


if __name__ == "__main__":
    asyncio.run(main())
