"""Tenant scoping for the real shop and the portfolio demo sandboxes.

The domain already carried a nullable ``shop_id`` as the seam for a future
multi-shop product. The demo puts that seam to work: a sandbox is simply a
tenant whose ``shop_id`` is its session token. The real shop keeps
``shop_id IS NULL``.

Every repository filters on the tenant, so a demo visitor can never read
or write the real shop's rows, and two visitors can never see each other.
"""

from dataclasses import dataclass
from typing import Any

from sqlalchemy import Select


@dataclass(frozen=True, slots=True)
class Tenant:
    """Which shop a request is allowed to touch."""

    shop_id: str | None
    is_demo: bool = False

    @classmethod
    def real(cls) -> "Tenant":
        """Return the tenant of the shop that actually runs the app."""
        return cls(shop_id=None, is_demo=False)

    @classmethod
    def demo(cls, session_id: str) -> "Tenant":
        """Return the tenant of one demo sandbox."""
        return cls(shop_id=session_id, is_demo=True)

    def owns(self, shop_id: str | None) -> bool:
        """Return True when a row belongs to this tenant."""
        return shop_id == self.shop_id


def scope(statement: Select, column: Any, tenant: Tenant) -> Select:
    """Restrict a query to one tenant.

    ``IS NULL`` is used for the real shop rather than ``= NULL`` because
    SQL equality against NULL never matches.
    """
    if tenant.shop_id is None:
        return statement.where(column.is_(None))
    return statement.where(column == tenant.shop_id)
