"""Appointment data access."""

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.appointment import Appointment
from models.enums import BLOCKING_STATUSES, AppointmentStatus
from models.user import User
from repositories.base import BaseRepository


class AppointmentRepository(BaseRepository[Appointment]):
    """Data access for appointments."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize repository for the Appointment model."""
        super().__init__(db, Appointment)

    @staticmethod
    def _with_relations(statement: Select) -> Select:
        """Eager load everything the read schema needs."""
        return statement.options(
            selectinload(Appointment.service),
            selectinload(Appointment.extras),
            selectinload(Appointment.customer).selectinload(
                User.customer_profile
            ),
            selectinload(Appointment.barber).selectinload(
                User.barber_profile
            ),
        )

    async def get_detail(self, appointment_id: str) -> Appointment | None:
        """Return one appointment with related entities loaded."""
        statement = self._with_relations(
            select(Appointment).where(Appointment.id == appointment_id)
        )
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    def _apply_filters(
        self,
        statement: Select,
        *,
        customer_id: str | None,
        barber_id: str | None,
        date_from: datetime | None,
        date_to: datetime | None,
        statuses: Sequence[AppointmentStatus] | None,
    ) -> Select:
        """Apply the shared appointment filters to a query."""
        if customer_id:
            statement = statement.where(
                Appointment.customer_id == customer_id
            )
        if barber_id:
            statement = statement.where(Appointment.barber_id == barber_id)
        if date_from:
            statement = statement.where(Appointment.starts_at >= date_from)
        if date_to:
            statement = statement.where(Appointment.starts_at < date_to)
        if statuses:
            statement = statement.where(Appointment.status.in_(statuses))
        return statement

    async def search(
        self,
        *,
        customer_id: str | None = None,
        barber_id: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        statuses: Sequence[AppointmentStatus] | None = None,
        limit: int = 50,
        offset: int = 0,
        newest_first: bool = False,
    ) -> tuple[list[Appointment], int]:
        """Return a filtered page of appointments plus the total count."""
        filters = {
            "customer_id": customer_id,
            "barber_id": barber_id,
            "date_from": date_from,
            "date_to": date_to,
            "statuses": statuses,
        }

        count_statement = self._apply_filters(
            select(func.count()).select_from(Appointment),
            **filters,
        )
        total = int((await self.db.execute(count_statement)).scalar_one())

        order = (
            Appointment.starts_at.desc()
            if newest_first
            else Appointment.starts_at.asc()
        )
        page_statement = self._with_relations(
            self._apply_filters(select(Appointment), **filters)
            .order_by(order)
            .limit(limit)
            .offset(offset)
        )
        rows = (await self.db.execute(page_statement)).scalars().all()
        return list(rows), total

    async def list_blocking_for_barbers(
        self,
        barber_ids: Sequence[str],
        *,
        window_start: datetime,
        window_end: datetime,
    ) -> list[Appointment]:
        """Return active appointments overlapping the requested window."""
        if not barber_ids:
            return []
        statement = (
            select(Appointment)
            .where(Appointment.barber_id.in_(barber_ids))
            .where(Appointment.status.in_(tuple(BLOCKING_STATUSES)))
            .where(Appointment.starts_at < window_end)
            .where(Appointment.ends_at > window_start)
            .order_by(Appointment.starts_at)
        )
        result = await self.db.execute(statement)
        return list(result.scalars().all())

    async def has_conflict(
        self,
        *,
        barber_id: str,
        starts_at: datetime,
        ends_at: datetime,
        exclude_id: str | None = None,
    ) -> bool:
        """Return True when the barber already has an overlapping slot."""
        statement = (
            select(Appointment.id)
            .where(Appointment.barber_id == barber_id)
            .where(Appointment.status.in_(tuple(BLOCKING_STATUSES)))
            .where(Appointment.starts_at < ends_at)
            .where(Appointment.ends_at > starts_at)
            .limit(1)
        )
        if exclude_id:
            statement = statement.where(Appointment.id != exclude_id)
        result = await self.db.execute(statement)
        return result.first() is not None

    async def count_by_status(
        self,
        *,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        barber_id: str | None = None,
    ) -> dict[AppointmentStatus, int]:
        """Return appointment counts grouped by status."""
        statement = self._apply_filters(
            select(Appointment.status, func.count()).group_by(
                Appointment.status
            ),
            customer_id=None,
            barber_id=barber_id,
            date_from=date_from,
            date_to=date_to,
            statuses=None,
        )
        result = await self.db.execute(statement)
        return {
            AppointmentStatus(status): int(count)
            for status, count in result.all()
        }

    async def completed_revenue_cents(
        self,
        *,
        date_from: datetime,
        date_to: datetime,
        barber_id: str | None = None,
    ) -> int:
        """Return revenue booked by appointments marked as completed."""
        total = (
            Appointment.service_price_cents
            + Appointment.extras_price_cents
            + Appointment.tip_cents
        )
        statement = (
            select(func.coalesce(func.sum(total), 0))
            .where(Appointment.status == AppointmentStatus.COMPLETED)
            .where(Appointment.starts_at >= date_from)
            .where(Appointment.starts_at < date_to)
        )
        if barber_id:
            statement = statement.where(Appointment.barber_id == barber_id)
        result = await self.db.execute(statement)
        return int(result.scalar_one())
