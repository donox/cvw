"""Add dynamic group fields

Revision ID: 2896ef34b10a
Revises: c7d4e2b1a903
Create Date: 2026-03-26 11:14:35.189334

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2896ef34b10a'
down_revision: Union[str, None] = 'c7d4e2b1a903'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('member_groups', sa.Column('is_dynamic', sa.Boolean(), nullable=True))
    op.add_column('member_groups', sa.Column('filter_criteria', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('member_groups', 'filter_criteria')
    op.drop_column('member_groups', 'is_dynamic')
    op.create_table('content_blocks',
    sa.Column('key', sa.VARCHAR(), nullable=False),
    sa.Column('title', sa.VARCHAR(), nullable=False),
    sa.Column('body', sa.VARCHAR(), nullable=True),
    sa.Column('updated_at', sa.DATETIME(), nullable=True),
    sa.PrimaryKeyConstraint('key')
    )
    op.create_table('attendance',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('org_event_id', sa.INTEGER(), nullable=False),
    sa.Column('member_id', sa.INTEGER(), nullable=True),
    sa.Column('visitor_name', sa.VARCHAR(length=100), nullable=True),
    sa.Column('visitor_email', sa.VARCHAR(length=200), nullable=True),
    sa.Column('attendance_type', sa.VARCHAR(length=20), nullable=True),
    sa.Column('checked_in_at', sa.DATETIME(), nullable=True),
    sa.Column('recorded_by', sa.VARCHAR(length=100), nullable=True),
    sa.ForeignKeyConstraint(['member_id'], ['members.id'], ),
    sa.ForeignKeyConstraint(['org_event_id'], ['org_events.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('event_registrations',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('org_event_id', sa.INTEGER(), nullable=False),
    sa.Column('member_id', sa.INTEGER(), nullable=True),
    sa.Column('name', sa.VARCHAR(length=100), nullable=False),
    sa.Column('email', sa.VARCHAR(length=200), nullable=False),
    sa.Column('attendance_type', sa.VARCHAR(length=20), nullable=True),
    sa.Column('status', sa.VARCHAR(length=20), nullable=True),
    sa.Column('waitlist_position', sa.INTEGER(), nullable=True),
    sa.Column('cancel_token', sa.VARCHAR(length=64), nullable=True),
    sa.Column('registered_at', sa.DATETIME(), nullable=True),
    sa.Column('confirmed_at', sa.DATETIME(), nullable=True),
    sa.Column('notes', sa.VARCHAR(length=500), nullable=True),
    sa.ForeignKeyConstraint(['member_id'], ['members.id'], ),
    sa.ForeignKeyConstraint(['org_event_id'], ['org_events.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('cancel_token')
    )
    op.create_table('apscheduler_jobs',
    sa.Column('id', sa.VARCHAR(length=191), nullable=False),
    sa.Column('next_run_time', sa.FLOAT(), nullable=True),
    sa.Column('job_state', sa.BLOB(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_apscheduler_jobs_next_run_time', 'apscheduler_jobs', ['next_run_time'], unique=False)
    op.create_table('resources',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('category', sa.VARCHAR(length=100), nullable=False),
    sa.Column('title', sa.VARCHAR(length=200), nullable=False),
    sa.Column('url', sa.VARCHAR(length=1000), nullable=False),
    sa.Column('description', sa.VARCHAR(length=500), nullable=True),
    sa.Column('sort_order', sa.INTEGER(), nullable=True),
    sa.Column('active', sa.BOOLEAN(), nullable=True),
    sa.Column('created_at', sa.DATETIME(), nullable=True),
    sa.Column('updated_at', sa.DATETIME(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_resources_category', 'resources', ['category'], unique=False)
    op.create_table('public_pages',
    sa.Column('slug', sa.VARCHAR(), nullable=False),
    sa.Column('label', sa.VARCHAR(), nullable=False),
    sa.Column('members_only', sa.BOOLEAN(), nullable=False),
    sa.PrimaryKeyConstraint('slug')
    )
    op.create_table('site_settings',
    sa.Column('key', sa.VARCHAR(), nullable=False),
    sa.Column('label', sa.VARCHAR(), nullable=False),
    sa.Column('value', sa.VARCHAR(), nullable=True),
    sa.Column('updated_at', sa.DATETIME(), nullable=True),
    sa.PrimaryKeyConstraint('key')
    )
    # ### end Alembic commands ###
