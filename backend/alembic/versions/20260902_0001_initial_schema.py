"""Initial BarberApp schema.

Revision ID: 20260902_0001
Revises:
Create Date: 2026-09-02

Creates the full domain: accounts and profiles, catalog, opening hours,
barber time off, appointments and payments.

On PostgreSQL the migration also installs ``btree_gist`` and an EXCLUDE
constraint so two active appointments can never overlap for the same
barber. That guarantee lives in the database, not only in the service
layer, so a race between two concurrent bookings cannot double-book.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260902_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


user_role = sa.Enum("admin", "barber", "customer", name="user_role")
appointment_status = sa.Enum(
    "pending",
    "confirmed",
    "cancelled",
    "completed",
    "no_show",
    name="appointment_status",
)
payment_method = sa.Enum(
    "cash",
    "transfer",
    "card",
    "mercado_pago",
    name="payment_method",
)
payment_status = sa.Enum(
    "pending",
    "paid",
    "failed",
    "refunded",
    name="payment_status",
)


def _timestamps() -> list[sa.Column]:
    """Return fresh timestamp columns for one table definition."""
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    """Create the initial domain schema."""
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("shop_id", sa.String(length=36), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_shop_id", "users", ["shop_id"])
    op.create_index("ix_users_role", "users", ["role"])

    op.create_table(
        "barber_profiles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("phone", sa.String(length=40), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "customer_profiles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=True),
        sa.Column("phone", sa.String(length=40), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "business_hours",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("shop_id", sa.String(length=36), nullable=True),
        sa.Column("weekday", sa.Integer(), nullable=False),
        sa.Column("opens_at", sa.Time(), nullable=False),
        sa.Column("closes_at", sa.Time(), nullable=False),
        sa.Column("is_closed", sa.Boolean(), nullable=False),
        *_timestamps(),
        sa.CheckConstraint(
            "weekday >= 0 AND weekday <= 6",
            name="ck_business_hours_weekday",
        ),
        sa.CheckConstraint(
            "is_closed OR opens_at < closes_at",
            name="ck_business_hours_window",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "shop_id",
            "weekday",
            name="uq_business_hours_day",
        ),
    )
    op.create_index("ix_business_hours_shop_id", "business_hours", ["shop_id"])

    op.create_table(
        "barber_time_off",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("barber_id", sa.String(length=36), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        *_timestamps(),
        sa.CheckConstraint(
            "starts_at < ends_at",
            name="ck_barber_time_off_window",
        ),
        sa.ForeignKeyConstraint(
            ["barber_id"],
            ["barber_profiles.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_barber_time_off_barber_start",
        "barber_time_off",
        ["barber_id", "starts_at"],
    )

    op.create_table(
        "services",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("shop_id", sa.String(length=36), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *_timestamps(),
        sa.CheckConstraint(
            "duration_minutes > 0",
            name="ck_services_duration_positive",
        ),
        sa.CheckConstraint(
            "price_cents >= 0",
            name="ck_services_price_non_negative",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_services_shop_id", "services", ["shop_id"])
    op.create_index("ix_services_is_active", "services", ["is_active"])

    op.create_table(
        "product_extras",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("shop_id", sa.String(length=36), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *_timestamps(),
        sa.CheckConstraint(
            "duration_minutes >= 0",
            name="ck_extras_duration_non_negative",
        ),
        sa.CheckConstraint(
            "price_cents >= 0",
            name="ck_extras_price_non_negative",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_product_extras_shop_id", "product_extras", ["shop_id"])
    op.create_index(
        "ix_product_extras_is_active",
        "product_extras",
        ["is_active"],
    )

    op.create_table(
        "appointments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("shop_id", sa.String(length=36), nullable=True),
        sa.Column("customer_id", sa.String(length=36), nullable=False),
        sa.Column("barber_id", sa.String(length=36), nullable=False),
        sa.Column("service_id", sa.String(length=36), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("status", appointment_status, nullable=False),
        sa.Column("service_price_cents", sa.Integer(), nullable=False),
        sa.Column("extras_price_cents", sa.Integer(), nullable=False),
        sa.Column("payment_method", payment_method, nullable=True),
        sa.Column("payment_status", payment_status, nullable=False),
        sa.Column("tip_cents", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("cancellation_reason", sa.String(length=255), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.CheckConstraint(
            "duration_minutes > 0",
            name="ck_appointments_duration_positive",
        ),
        sa.CheckConstraint(
            "ends_at > starts_at",
            name="ck_appointments_window",
        ),
        sa.CheckConstraint(
            "tip_cents >= 0",
            name="ck_appointments_tip_non_negative",
        ),
        sa.CheckConstraint(
            "service_price_cents >= 0 AND extras_price_cents >= 0",
            name="ck_appointments_prices_non_negative",
        ),
        sa.CheckConstraint(
            "customer_id <> barber_id",
            name="ck_appointments_distinct_parties",
        ),
        sa.ForeignKeyConstraint(
            ["barber_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["service_id"],
            ["services.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_appointments_shop_id", "appointments", ["shop_id"])
    op.create_index(
        "ix_appointments_barber_starts",
        "appointments",
        ["barber_id", "starts_at"],
    )
    op.create_index(
        "ix_appointments_customer_starts",
        "appointments",
        ["customer_id", "starts_at"],
    )
    op.create_index(
        "ix_appointments_status_starts",
        "appointments",
        ["status", "starts_at"],
    )

    op.create_table(
        "appointment_extras",
        sa.Column("appointment_id", sa.String(length=36), nullable=False),
        sa.Column("extra_id", sa.String(length=36), nullable=False),
        sa.Column(
            "price_cents",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["appointment_id"],
            ["appointments.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["extra_id"],
            ["product_extras.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("appointment_id", "extra_id"),
    )

    op.create_table(
        "payments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("appointment_id", sa.String(length=36), nullable=False),
        sa.Column("method", payment_method, nullable=False),
        sa.Column("status", payment_status, nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("tip_cents", sa.Integer(), nullable=False),
        sa.Column("external_reference", sa.String(length=255), nullable=True),
        *_timestamps(),
        sa.CheckConstraint(
            "amount_cents >= 0 AND tip_cents >= 0",
            name="ck_payments_amounts_non_negative",
        ),
        sa.ForeignKeyConstraint(
            ["appointment_id"],
            ["appointments.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("appointment_id"),
    )

    _create_overlap_guard()


def _create_overlap_guard() -> None:
    """Add the PostgreSQL no-overlap constraint for active bookings."""
    if op.get_bind().dialect.name != "postgresql":
        return

    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.execute(
        "ALTER TABLE appointments "
        "ADD CONSTRAINT ex_appointments_no_overlap "
        "EXCLUDE USING gist ("
        "barber_id WITH =, "
        "tstzrange(starts_at, ends_at) WITH &&"
        ") WHERE (status IN ('pending', 'confirmed'))"
    )


def downgrade() -> None:
    """Drop the initial domain schema."""
    if op.get_bind().dialect.name == "postgresql":
        op.execute(
            "ALTER TABLE appointments "
            "DROP CONSTRAINT IF EXISTS ex_appointments_no_overlap"
        )

    op.drop_table("payments")
    op.drop_table("appointment_extras")
    op.drop_table("appointments")
    op.drop_table("product_extras")
    op.drop_table("services")
    op.drop_table("barber_time_off")
    op.drop_table("business_hours")
    op.drop_table("customer_profiles")
    op.drop_table("barber_profiles")
    op.drop_table("users")

    bind = op.get_bind()
    payment_status.drop(bind, checkfirst=True)
    payment_method.drop(bind, checkfirst=True)
    appointment_status.drop(bind, checkfirst=True)
    user_role.drop(bind, checkfirst=True)
