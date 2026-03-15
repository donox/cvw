"""add member_id and must_change_password to users

Revision ID: b4ef7d2a13e9
Revises: 6b9a8190d88d
Create Date: 2026-03-15 15:06:46.457186

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b4ef7d2a13e9'
down_revision: Union[str, None] = '6b9a8190d88d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('must_change_password', sa.Boolean(), nullable=True, server_default='0'))
        batch_op.add_column(sa.Column('member_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_users_member_id', 'members', ['member_id'], ['id'])


def downgrade() -> None:
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_constraint('fk_users_member_id', type_='foreignkey')
        batch_op.drop_column('member_id')
        batch_op.drop_column('must_change_password')
