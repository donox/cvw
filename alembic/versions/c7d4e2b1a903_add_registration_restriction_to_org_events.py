"""add_registration_restriction_to_org_events

Revision ID: c7d4e2b1a903
Revises: e3c1a92f8b05
Create Date: 2026-03-17 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c7d4e2b1a903'
down_revision: Union[str, None] = 'e3c1a92f8b05'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "org_events",
        sa.Column("registration_restriction", sa.String(20), nullable=True),
    )


def downgrade() -> None:
    with op.batch_alter_table("org_events") as batch_op:
        batch_op.drop_column("registration_restriction")
