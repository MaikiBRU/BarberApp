"""Widen the tenant identifier column.

Revision ID: 20260903_0003
Revises: 20260903_0002
Create Date: 2026-09-03

``shop_id`` was sized for a UUID, but it holds a tenant identifier: a
demo sandbox uses a 43-character URL-safe token. SQLite ignores VARCHAR
lengths, so this only surfaced against PostgreSQL.

Widening a varchar is a metadata-only change in PostgreSQL, so this runs
instantly and rewrites no rows.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260903_0003"
down_revision: str | None = "20260903_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = (
    "users",
    "services",
    "product_extras",
    "business_hours",
    "appointments",
)


def _alter(new_length: int, old_length: int) -> None:
    """Resize shop_id on every tenant-scoped table.

    Batch mode keeps the two dialects in step: PostgreSQL gets a plain
    metadata-only ALTER, and SQLite -- which has no ALTER COLUMN TYPE --
    gets the table rebuild it needs, so the schema matches the models on
    both.
    """
    for table in TABLES:
        with op.batch_alter_table(table) as batch:
            batch.alter_column(
                "shop_id",
                existing_type=sa.String(length=old_length),
                type_=sa.String(length=new_length),
                existing_nullable=True,
            )


def upgrade() -> None:
    """Grow shop_id from 36 to 64 characters."""
    _alter(new_length=64, old_length=36)


def downgrade() -> None:
    """Shrink shop_id back to 36 characters.

    Any demo sandbox rows must be gone first: their identifiers do not
    fit, and PostgreSQL will refuse the change while they exist.
    """
    _alter(new_length=36, old_length=64)
