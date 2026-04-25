"""add activity group fields

Revision ID: b3f8a1c2d9e4
Revises: a1b2c3d4e5f6
Create Date: 2026-04-25 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'b3f8a1c2d9e4'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── MemberGroup: activity fields ─────────────────────────────────────────
    op.add_column('member_groups', sa.Column('is_activity',       sa.Boolean(), nullable=True, server_default=sa.false()))
    op.add_column('member_groups', sa.Column('slug',              sa.String(),  nullable=True))
    op.add_column('member_groups', sa.Column('meeting_day',       sa.String(),  nullable=True))
    op.add_column('member_groups', sa.Column('meeting_frequency', sa.String(),  nullable=True))
    op.add_column('member_groups', sa.Column('google_group_url',  sa.String(),  nullable=True))

    # ── GroupLeader table ─────────────────────────────────────────────────────
    op.create_table(
        'group_leaders',
        sa.Column('id',         sa.Integer(),  nullable=False),
        sa.Column('group_id',   sa.Integer(),  nullable=False),
        sa.Column('member_id',  sa.Integer(),  nullable=False),
        sa.Column('role',       sa.String(),   nullable=True),
        sa.Column('event_id',   sa.Integer(),  nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['group_id'],  ['member_groups.id']),
        sa.ForeignKeyConstraint(['member_id'], ['members.id']),
        sa.ForeignKeyConstraint(['event_id'],  ['org_events.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # ── OrgEvent: activity group + planning notes ─────────────────────────────
    op.add_column('org_events', sa.Column('activity_group_id', sa.Integer(), nullable=True))
    op.add_column('org_events', sa.Column('planning_notes',    sa.Text(),    nullable=True))

    # ── Resource: optional group scope ────────────────────────────────────────
    op.add_column('resources', sa.Column('group_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('resources', 'group_id')

    op.drop_column('org_events', 'planning_notes')
    op.drop_column('org_events', 'activity_group_id')

    op.drop_table('group_leaders')

    op.drop_column('member_groups', 'google_group_url')
    op.drop_column('member_groups', 'meeting_frequency')
    op.drop_column('member_groups', 'meeting_day')
    op.drop_column('member_groups', 'slug')
    op.drop_column('member_groups', 'is_activity')
