"""add show_on_public to programs

Revision ID: 6b9a8190d88d
Revises: 2e555eaa64b3
Create Date: 2026-03-15 12:34:40.522667

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6b9a8190d88d'
down_revision: Union[str, None] = '2e555eaa64b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('programs') as batch_op:
        batch_op.add_column(sa.Column('show_on_public', sa.Boolean(), nullable=True, server_default='0'))


def downgrade() -> None:
    with op.batch_alter_table('programs') as batch_op:
        batch_op.drop_column('show_on_public')
