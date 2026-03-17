"""add_site_settings_and_content_blocks

Revision ID: da678a9fdbd3
Revises: b200a8406d2d
Create Date: 2026-03-17 02:58:08.867110

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'da678a9fdbd3'
down_revision: Union[str, None] = 'b200a8406d2d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "site_settings",
        sa.Column("key",        sa.String(), primary_key=True),
        sa.Column("label",      sa.String(), nullable=False),
        sa.Column("value",      sa.String(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "content_blocks",
        sa.Column("key",        sa.String(), primary_key=True),
        sa.Column("title",      sa.String(), nullable=False),
        sa.Column("body",       sa.String(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("content_blocks")
    op.drop_table("site_settings")
