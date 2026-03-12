"""officer nullable member, add category and notes

Revision ID: 1dd8f27f0805
Revises: 85e32c152a76
Create Date: 2026-03-12 18:08:23.084084

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1dd8f27f0805'
down_revision: Union[str, None] = '85e32c152a76'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('officers', sa.Column('category', sa.String(), nullable=True))
    op.add_column('officers', sa.Column('notes', sa.String(), nullable=True))
    with op.batch_alter_table('officers') as batch_op:
        batch_op.alter_column('member_id', existing_type=sa.INTEGER(), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table('officers') as batch_op:
        batch_op.alter_column('member_id', existing_type=sa.INTEGER(), nullable=False)
    op.drop_column('officers', 'notes')
    op.drop_column('officers', 'category')
