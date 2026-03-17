"""add_show_on_public_to_org_events_and_org_event_id_to_programs

Revision ID: b200a8406d2d
Revises: 3d2507459d2f
Create Date: 2026-03-16 16:18:22.233873

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b200a8406d2d'
down_revision: Union[str, None] = '3d2507459d2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("org_events") as batch_op:
        batch_op.add_column(sa.Column("show_on_public", sa.Boolean(), nullable=True, server_default=sa.false()))

    with op.batch_alter_table("programs") as batch_op:
        batch_op.add_column(sa.Column("org_event_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_programs_org_event_id", "org_events", ["org_event_id"], ["id"])


def downgrade() -> None:
    with op.batch_alter_table("programs") as batch_op:
        batch_op.drop_constraint("fk_programs_org_event_id", type_="foreignkey")
        batch_op.drop_column("org_event_id")

    with op.batch_alter_table("org_events") as batch_op:
        batch_op.drop_column("show_on_public")
