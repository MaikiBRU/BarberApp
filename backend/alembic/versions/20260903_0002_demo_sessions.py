"""Portfolio demo sandboxes.

Revision ID: 20260903_0002
Revises: 20260902_0001
Create Date: 2026-09-03

Adds the sandbox registry. No other table changes: a sandbox reuses the
nullable ``shop_id`` that the domain already carried as its multi-shop
seam, so demo rows and real rows live in the same tables, separated by
tenant on every query.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260903_0002"
down_revision: str | None = "20260902_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the demo session registry."""
    op.create_table(
        "demo_sessions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=60), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.Column("appointments_created", sa.Integer(), nullable=False),
        sa.Column("writes_used", sa.Integer(), nullable=False),
        sa.Column("created_ip_hash", sa.String(length=64), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_demo_sessions_expires_at",
        "demo_sessions",
        ["expires_at"],
    )


def downgrade() -> None:
    """Drop the demo session registry."""
    op.drop_index("ix_demo_sessions_expires_at", table_name="demo_sessions")
    op.drop_table("demo_sessions")
