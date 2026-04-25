"""add group_documents table

Revision ID: 889308198d9b
Revises: b3f8a1c2d9e4
Create Date: 2026-04-25 16:25:29.282695

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '889308198d9b'
down_revision: Union[str, None] = 'b3f8a1c2d9e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'group_documents',
        sa.Column('id',         sa.Integer(),     nullable=False),
        sa.Column('group_id',   sa.Integer(),     nullable=False),
        sa.Column('title',      sa.String(200),   nullable=False),
        sa.Column('body',       sa.Text(),        nullable=False, server_default=''),
        sa.Column('sort_order', sa.Integer(),     nullable=True),
        sa.Column('created_at', sa.DateTime(),    nullable=True),
        sa.Column('updated_at', sa.DateTime(),    nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['member_groups.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('group_documents')
