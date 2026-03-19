"""add_public_pages

Revision ID: e3c1a92f8b05
Revises: da678a9fdbd3
Create Date: 2026-03-17 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e3c1a92f8b05'
down_revision: Union[str, None] = 'da678a9fdbd3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "public_pages",
        sa.Column("slug",         sa.String(),  primary_key=True),
        sa.Column("label",        sa.String(),  nullable=False),
        sa.Column("members_only", sa.Boolean(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("public_pages")
