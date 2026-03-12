"""add payment fields to members, make email nullable

Revision ID: 3e1dd292f70e
Revises: 90a4f9b5b7bf
Create Date: 2026-03-12 15:57:28.504984

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3e1dd292f70e'
down_revision: Union[str, None] = '90a4f9b5b7bf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('members', sa.Column('dues_amount', sa.Float(), nullable=True))
    op.add_column('members', sa.Column('donation', sa.Float(), nullable=True))
    op.add_column('members', sa.Column('payment_method', sa.String(), nullable=True))
    with op.batch_alter_table('members') as batch_op:
        batch_op.alter_column('email', existing_type=sa.VARCHAR(), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table('members') as batch_op:
        batch_op.alter_column('email', existing_type=sa.VARCHAR(), nullable=False)
    op.drop_column('members', 'payment_method')
    op.drop_column('members', 'donation')
    op.drop_column('members', 'dues_amount')
