"""add template_type to email_templates

Revision ID: f1ca6de276d6
Revises: b4ef7d2a13e9
Create Date: 2026-03-15 15:31:28.923701

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1ca6de276d6'
down_revision: Union[str, None] = 'b4ef7d2a13e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('email_templates') as batch_op:
        batch_op.add_column(sa.Column('template_type', sa.String(),
                                      nullable=True, server_default='simple'))


def downgrade() -> None:
    with op.batch_alter_table('email_templates') as batch_op:
        batch_op.drop_column('template_type')
