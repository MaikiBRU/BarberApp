"""Anonymous sandbox sessions for the portfolio demo."""

from datetime import datetime

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base, TimestampMixin, utc_now
from models.types import UTCDateTime


class DemoSession(TimestampMixin, Base):
    """A short-lived, self-contained shop created for one visitor.

    The primary key is a URL-safe random token rather than a sequence, so
    sandbox identifiers cannot be guessed or enumerated. Every row the
    sandbox owns carries this id in its ``shop_id`` column.
    """

    __tablename__ = "demo_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    label: Mapped[str] = mapped_column(String(60), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        index=True,
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        default=utc_now,
        nullable=False,
    )
    revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Quota counters, incremented server-side only.
    appointments_created: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    writes_used: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Coarse abuse signal. Never returned by the API.
    created_ip_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )
