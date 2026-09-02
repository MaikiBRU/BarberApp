"""Lifecycle for the anonymous portfolio demo sandboxes.

A sandbox is a self-contained shop. Every row it creates carries its id
in ``shop_id`` and every read is filtered by that id, so two visitors can
never observe each other and neither can reach the real shop.

Sessions end by absolute TTL and by idle timeout, and both are checked on
every request rather than trusting the cleanup pass to have already run.
"""

import hashlib
import secrets
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from exceptions.errors import AppError
from middleware.rate_limit import SlidingWindowCounter
from models.appointment import Appointment, Payment
from models.demo import DemoSession
from models.schedule import BarberTimeOff, BusinessHours
from models.service import ProductExtra, Service
from models.user import BarberProfile, User
from repositories.demo import DemoSessionRepository

ADJECTIVES = ("agil", "claro", "nitido", "sereno", "vivo", "firme", "lucido")
NOUNS = ("delta", "cauce", "prisma", "vertice", "umbral", "nodo", "matiz")


class DemoDisabled(AppError):
    """The demo sandbox is switched off by configuration."""

    status_code = 404
    error_type = "not_found"


class DemoRateLimited(AppError):
    """Too many sandboxes requested from the same origin."""

    status_code = 429
    error_type = "rate_limit_exceeded"


class DemoCapacityReached(AppError):
    """The global cap on concurrent sandboxes is full."""

    status_code = 503
    error_type = "demo_capacity_reached"


class DemoQuotaExceeded(AppError):
    """A per-sandbox limit was reached."""

    status_code = 429
    error_type = "demo_quota_exceeded"


@dataclass(frozen=True, slots=True)
class SessionState:
    """Snapshot of a sandbox, safe to serialize to the client."""

    label: str
    expires_at: datetime
    seconds_remaining: int
    idle_seconds_remaining: int
    appointments_used: int
    appointments_max: int
    writes_used: int
    writes_max: int


_session_limiter = SlidingWindowCounter(
    get_settings().demo_rate_limit_per_hour or 1,
    3600,
)


def hash_client(value: str | None) -> str | None:
    """Return a salted hash of a client address, or None."""
    if not value:
        return None
    salted = f"{get_settings().jwt_secret_key}:{value}".encode()
    return hashlib.sha256(salted).hexdigest()


def new_label() -> str:
    """Return a friendly, non-identifying name for a sandbox."""
    adjective = secrets.choice(ADJECTIVES)
    noun = secrets.choice(NOUNS)
    return f"{noun}-{adjective}"


def reset_rate_limit() -> None:
    """Drop the creation counters. Used by tests."""
    _session_limiter.reset()


def _check_rate_limit(client_key: str | None) -> None:
    """Reject repeated sandbox creation from one origin."""
    settings = get_settings()
    if not client_key or settings.demo_rate_limit_per_hour <= 0:
        return

    # Rebuilt from settings so a test that changes the limit is honoured.
    _session_limiter.max_requests = settings.demo_rate_limit_per_hour
    if _session_limiter.check(client_key, time.monotonic()) is not None:
        raise DemoRateLimited(
            "Ya creaste varias demos desde esta conexión. "
            "Probá de nuevo en un rato.",
        )


async def create_session(
    db: AsyncSession,
    *,
    client_ip: str | None = None,
) -> DemoSession:
    """Mint an empty sandbox, enforcing the abuse controls first."""
    settings = get_settings()
    if not settings.demo_enabled:
        raise DemoDisabled("La demo no está disponible.")

    _check_rate_limit(client_ip)

    now = datetime.now(UTC)
    repository = DemoSessionRepository(db)
    active = await repository.count_active(now=now)
    if active >= settings.demo_max_active_sessions:
        raise DemoCapacityReached(
            "La demo alcanzó su capacidad máxima. "
            "Probá de nuevo en unos minutos.",
        )

    session = DemoSession(
        id=secrets.token_urlsafe(32),
        label=new_label(),
        expires_at=now + timedelta(minutes=settings.demo_session_ttl_minutes),
        last_seen_at=now,
        created_ip_hash=hash_client(client_ip),
    )
    db.add(session)
    await db.flush()
    return session


def describe(session: DemoSession) -> SessionState:
    """Return everything the interface shows about a sandbox."""
    settings = get_settings()
    now = datetime.now(UTC)
    idle_deadline = session.last_seen_at + timedelta(
        minutes=settings.demo_idle_timeout_minutes,
    )
    return SessionState(
        label=session.label,
        expires_at=session.expires_at,
        seconds_remaining=max(
            int((session.expires_at - now).total_seconds()), 0
        ),
        idle_seconds_remaining=max(
            int((idle_deadline - now).total_seconds()), 0
        ),
        appointments_used=session.appointments_created,
        appointments_max=settings.demo_max_appointments,
        writes_used=session.writes_used,
        writes_max=settings.demo_max_writes,
    )


async def register_appointment(db: AsyncSession, session: DemoSession) -> None:
    """Count one booking against the sandbox quota."""
    settings = get_settings()
    if session.appointments_created >= settings.demo_max_appointments:
        raise DemoQuotaExceeded(
            "Llegaste al límite de turnos de la demo "
            f"({settings.demo_max_appointments}). "
            "Reiniciá la demo para seguir probando.",
        )
    session.appointments_created += 1
    await db.flush()


async def register_write(db: AsyncSession, session: DemoSession) -> None:
    """Count one modification against the sandbox quota."""
    settings = get_settings()
    if session.writes_used >= settings.demo_max_writes:
        raise DemoQuotaExceeded(
            "Llegaste al límite de cambios de la demo "
            f"({settings.demo_max_writes}). "
            "Reiniciá la demo para seguir probando.",
        )
    session.writes_used += 1
    await db.flush()


async def purge_session_data(db: AsyncSession, session_id: str) -> int:
    """Delete every row a sandbox owns.

    Order follows the foreign keys: appointments reference users and
    services with ``ON DELETE RESTRICT``, so they go first. Profiles and
    appointment extras disappear through their cascades.
    """
    removed = 0

    user_ids = (
        select(User.id).where(User.shop_id == session_id).scalar_subquery()
    )
    appointment_ids = (
        select(Appointment.id)
        .where(Appointment.shop_id == session_id)
        .scalar_subquery()
    )
    barber_profile_ids = (
        select(BarberProfile.id)
        .where(BarberProfile.user_id.in_(user_ids))
        .scalar_subquery()
    )

    for statement in (
        delete(Payment).where(Payment.appointment_id.in_(appointment_ids)),
        delete(Appointment).where(Appointment.shop_id == session_id),
        delete(BarberTimeOff).where(
            BarberTimeOff.barber_id.in_(barber_profile_ids)
        ),
        delete(User).where(User.shop_id == session_id),
        delete(Service).where(Service.shop_id == session_id),
        delete(ProductExtra).where(ProductExtra.shop_id == session_id),
        delete(BusinessHours).where(BusinessHours.shop_id == session_id),
    ):
        result = await db.execute(statement)
        removed += result.rowcount or 0

    await db.flush()
    return removed


async def end_session(db: AsyncSession, session: DemoSession) -> int:
    """Wipe a sandbox and remove its registry row."""
    removed = await purge_session_data(db, session.id)
    await db.delete(session)
    await db.flush()
    return removed


async def reset_counters(db: AsyncSession, session: DemoSession) -> None:
    """Give a sandbox its full quota back after a reset."""
    session.appointments_created = 0
    session.writes_used = 0
    session.last_seen_at = datetime.now(UTC)
    await db.flush()


async def cleanup_expired(db: AsyncSession) -> int:
    """Remove sandboxes past their TTL. Safe to call repeatedly."""
    now = datetime.now(UTC)
    repository = DemoSessionRepository(db)
    removed = 0
    for session in await repository.list_expired(now=now):
        await end_session(db, session)
        removed += 1
    return removed


async def get_active_session(
    db: AsyncSession,
    tenant,
) -> DemoSession | None:
    """Return the live sandbox for a tenant, or None outside the demo."""
    if not tenant.is_demo or tenant.shop_id is None:
        return None

    settings = get_settings()
    now = datetime.now(UTC)
    return await DemoSessionRepository(db).get_active(
        tenant.shop_id,
        now=now,
        idle_cutoff=now
        - timedelta(minutes=settings.demo_idle_timeout_minutes),
    )
