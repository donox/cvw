"""add resource file_path

Revision ID: 02e50820f957
Revises: 2896ef34b10a
Create Date: 2026-03-27 11:49:52.938914

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '02e50820f957'
down_revision: Union[str, None] = '2896ef34b10a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('resources', sa.Column('file_path', sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column('resources', 'file_path')
