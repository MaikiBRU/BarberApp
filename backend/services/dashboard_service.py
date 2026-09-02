"""Operational dashboard metrics computed from stored rows."""

from datetime import UTC, date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from core.tenancy import Tenant
from models.enums import BLOCKING_STATUSES, AppointmentStatus, UserRole
from models.user import User
from repositories.appointments import AppointmentRepository
from repositories.catalog import ServiceRepository
from repositories.users import UserRepository
from schemas.appointment import AppointmentRead
from schemas.dashboard import AppointmentCounts, DashboardSummary
from services.appointment_view import to_read

NEXT_APPOINTMENTS_LIMIT = 5


class DashboardService:
    """Build the figures shown on the staff dashboard.

    Every number comes from a query against real rows. A barber sees
    only their own agenda; an administrator sees the whole shop.
    """

    def __init__(
        self,
        db: AsyncSession,
        tenant: Tenant | None = None,
    ) -> None:
        """Wire the repositories the dashboard reads from."""
        self.db = db
        self.tenant = tenant or Tenant.real()
        self.settings = get_settings()
        self.appointments = AppointmentRepository(db, self.tenant)
        self.services = ServiceRepository(db, self.tenant)
        self.users = UserRepository(db, self.tenant)

    async def get_summary(self, viewer: User) -> DashboardSummary:
        """Return today's operational figures for the viewer."""
        barber_filter = (
            viewer.id if viewer.role == UserRole.BARBER else None
        )
        today = self._local_today()
        day_start, day_end = self._local_day_bounds(today)
        month_start, month_end = self._local_month_bounds(today)

        counts = await self.appointments.count_by_status(
            date_from=day_start,
            date_to=day_end,
            barber_id=barber_filter,
        )
        upcoming, upcoming_total = await self.appointments.search(
            barber_id=barber_filter,
            date_from=day_end,
            statuses=sorted(BLOCKING_STATUSES),
            limit=NEXT_APPOINTMENTS_LIMIT,
            offset=0,
        )
        today_revenue = await self.appointments.completed_revenue_cents(
            date_from=day_start,
            date_to=day_end,
            barber_id=barber_filter,
        )
        month_revenue = await self.appointments.completed_revenue_cents(
            date_from=month_start,
            date_to=month_end,
            barber_id=barber_filter,
        )

        return DashboardSummary(
            date=today,
            today=self._to_counts(counts),
            upcoming_count=upcoming_total,
            today_revenue_cents=today_revenue,
            month_revenue_cents=month_revenue,
            active_barbers=await self.users.count_active_barbers(),
            active_services=await self.services.count_active(),
            currency=self.settings.currency,
            next_appointments=[
                to_read(appointment, viewer)
                for appointment in upcoming
            ],
        )

    async def list_today(self, viewer: User) -> list[AppointmentRead]:
        """Return every appointment scheduled for the local today."""
        barber_filter = (
            viewer.id if viewer.role == UserRole.BARBER else None
        )
        day_start, day_end = self._local_day_bounds(self._local_today())
        rows, _ = await self.appointments.search(
            barber_id=barber_filter,
            date_from=day_start,
            date_to=day_end,
            limit=200,
            offset=0,
        )
        return [
            to_read(appointment, viewer)
            for appointment in rows
        ]

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    @staticmethod
    def _to_counts(
        counts: dict[AppointmentStatus, int],
    ) -> AppointmentCounts:
        """Map grouped status counts into the response shape."""
        return AppointmentCounts(
            pending=counts.get(AppointmentStatus.PENDING, 0),
            confirmed=counts.get(AppointmentStatus.CONFIRMED, 0),
            completed=counts.get(AppointmentStatus.COMPLETED, 0),
            cancelled=counts.get(AppointmentStatus.CANCELLED, 0),
            no_show=counts.get(AppointmentStatus.NO_SHOW, 0),
        )

    def _local_today(self) -> date:
        """Return the current calendar date in the shop timezone."""
        return datetime.now(self.settings.timezone).date()

    def _local_day_bounds(self, day: date) -> tuple[datetime, datetime]:
        """Return the UTC bounds of one local calendar day."""
        tz = self.settings.timezone
        start = datetime.combine(day, datetime.min.time(), tzinfo=tz)
        return (
            start.astimezone(UTC),
            (start + timedelta(days=1)).astimezone(UTC),
        )

    def _local_month_bounds(self, day: date) -> tuple[datetime, datetime]:
        """Return the UTC bounds of the local calendar month."""
        tz = self.settings.timezone
        first = day.replace(day=1)
        next_month = (
            first.replace(year=first.year + 1, month=1)
            if first.month == 12
            else first.replace(month=first.month + 1)
        )
        start = datetime.combine(first, datetime.min.time(), tzinfo=tz)
        end = datetime.combine(next_month, datetime.min.time(), tzinfo=tz)
        return start.astimezone(UTC), end.astimezone(UTC)
