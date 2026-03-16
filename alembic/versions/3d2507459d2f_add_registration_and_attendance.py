"""add registration and attendance

Revision ID: 3d2507459d2f
Revises: 612f33209af2
Create Date: 2026-03-16 12:32:31.933350

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3d2507459d2f'
down_revision: Union[str, None] = '612f33209af2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add registration/zoom fields to existing org_events table
    with op.batch_alter_table("org_events") as batch_op:
        batch_op.add_column(sa.Column("zoom_url",             sa.String(500), nullable=True))
        batch_op.add_column(sa.Column("registration_enabled", sa.Boolean(),   nullable=True, server_default="0"))
        batch_op.add_column(sa.Column("capacity",             sa.Integer(),   nullable=True))
        batch_op.add_column(sa.Column("registration_note",    sa.String(500), nullable=True))

    op.create_table(
        "event_registrations",
        sa.Column("id",                sa.Integer(),   nullable=False),
        sa.Column("org_event_id",      sa.Integer(),   sa.ForeignKey("org_events.id"), nullable=False),
        sa.Column("member_id",         sa.Integer(),   sa.ForeignKey("members.id"),    nullable=True),
        sa.Column("name",              sa.String(100), nullable=False),
        sa.Column("email",             sa.String(200), nullable=False),
        sa.Column("attendance_type",   sa.String(20),  nullable=True),
        sa.Column("status",            sa.String(20),  nullable=True),
        sa.Column("waitlist_position", sa.Integer(),   nullable=True),
        sa.Column("cancel_token",      sa.String(64),  nullable=True),
        sa.Column("registered_at",     sa.DateTime(),  nullable=True),
        sa.Column("confirmed_at",      sa.DateTime(),  nullable=True),
        sa.Column("notes",             sa.String(500), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cancel_token"),
    )

    op.create_table(
        "attendance",
        sa.Column("id",              sa.Integer(),   nullable=False),
        sa.Column("org_event_id",    sa.Integer(),   sa.ForeignKey("org_events.id"), nullable=False),
        sa.Column("member_id",       sa.Integer(),   sa.ForeignKey("members.id"),    nullable=True),
        sa.Column("visitor_name",    sa.String(100), nullable=True),
        sa.Column("visitor_email",   sa.String(200), nullable=True),
        sa.Column("attendance_type", sa.String(20),  nullable=True),
        sa.Column("checked_in_at",   sa.DateTime(),  nullable=True),
        sa.Column("recorded_by",     sa.String(100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("attendance")
    op.drop_table("event_registrations")
    with op.batch_alter_table("org_events") as batch_op:
        batch_op.drop_column("registration_note")
        batch_op.drop_column("capacity")
        batch_op.drop_column("registration_enabled")
        batch_op.drop_column("zoom_url")
