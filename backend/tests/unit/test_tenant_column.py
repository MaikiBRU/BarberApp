"""The tenant column has to fit the identifiers we actually generate."""

import secrets

from models.appointment import Appointment
from models.schedule import BusinessHours
from models.service import ProductExtra, Service
from models.user import User

TENANT_MODELS = (User, Service, ProductExtra, BusinessHours, Appointment)


def demo_session_id() -> str:
    """Mirror how the demo mints a sandbox identifier."""
    return secrets.token_urlsafe(32)


def test_a_sandbox_id_fits_every_tenant_column() -> None:
    """SQLite ignores VARCHAR lengths; PostgreSQL does not.

    Without this check an oversized identifier only fails in production,
    which is exactly how it failed the first time.
    """
    length = len(demo_session_id())

    for model in TENANT_MODELS:
        column = model.__table__.columns["shop_id"]
        assert column.type.length >= length, (
            f"{model.__tablename__}.shop_id holds "
            f"{column.type.length} chars, needs {length}"
        )


def test_the_sandbox_id_is_long_enough_to_be_unguessable() -> None:
    """A tenant id doubles as a capability, so it must not be short."""
    assert len(demo_session_id()) >= 40


def test_the_demo_session_table_can_store_its_own_id() -> None:
    """The registry key and the tenant column must agree."""
    from models.demo import DemoSession

    assert DemoSession.__table__.columns["id"].type.length >= len(
        demo_session_id()
    )
