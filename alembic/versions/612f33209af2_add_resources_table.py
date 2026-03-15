"""add resources table

Revision ID: 612f33209af2
Revises: f1ca6de276d6
Create Date: 2026-03-15 18:17:02.592172

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '612f33209af2'
down_revision: Union[str, None] = 'f1ca6de276d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'resources',
        sa.Column('id',          sa.Integer(),      nullable=False),
        sa.Column('category',    sa.String(100),    nullable=False),
        sa.Column('title',       sa.String(200),    nullable=False),
        sa.Column('url',         sa.String(1000),   nullable=False),
        sa.Column('description', sa.String(500),    nullable=True),
        sa.Column('sort_order',  sa.Integer(),      nullable=True),
        sa.Column('active',      sa.Boolean(),      nullable=True),
        sa.Column('created_at',  sa.DateTime(),     nullable=True),
        sa.Column('updated_at',  sa.DateTime(),     nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_resources_category', 'resources', ['category'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_resources_category', table_name='resources')
    op.drop_table('resources')
