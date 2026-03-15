"""add member groups and email system

Revision ID: 2e555eaa64b3
Revises: 1dd8f27f0805
Create Date: 2026-03-15 06:28:04.292437

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '2e555eaa64b3'
down_revision: Union[str, None] = '1dd8f27f0805'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'member_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_index('ix_member_groups_id', 'member_groups', ['id'])

    op.create_table(
        'member_group_members',
        sa.Column('group_id', sa.Integer(), sa.ForeignKey('member_groups.id'), nullable=False, primary_key=True),
        sa.Column('member_id', sa.Integer(), sa.ForeignKey('members.id'), nullable=False, primary_key=True),
    )

    op.create_table(
        'email_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('body', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_index('ix_email_templates_id', 'email_templates', ['id'])

    op.create_table(
        'scheduled_emails',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('template_id', sa.Integer(), sa.ForeignKey('email_templates.id'), nullable=False),
        sa.Column('group_id', sa.Integer(), sa.ForeignKey('member_groups.id'), nullable=True),
        sa.Column('cron_minute', sa.String(), nullable=True),
        sa.Column('cron_hour', sa.String(), nullable=True),
        sa.Column('cron_day', sa.String(), nullable=True),
        sa.Column('cron_month', sa.String(), nullable=True),
        sa.Column('cron_day_of_week', sa.String(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True),
        sa.Column('last_run_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_scheduled_emails_id', 'scheduled_emails', ['id'])

    op.create_table(
        'email_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sent_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column('subject', sa.String(), nullable=True),
        sa.Column('recipient_count', sa.Integer(), nullable=True),
        sa.Column('group_id', sa.Integer(), sa.ForeignKey('member_groups.id'), nullable=True),
        sa.Column('template_id', sa.Integer(), sa.ForeignKey('email_templates.id'), nullable=True),
        sa.Column('sent_by', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('error_detail', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_email_logs_id', 'email_logs', ['id'])


def downgrade() -> None:
    op.drop_index('ix_email_logs_id', table_name='email_logs')
    op.drop_table('email_logs')
    op.drop_index('ix_scheduled_emails_id', table_name='scheduled_emails')
    op.drop_table('scheduled_emails')
    op.drop_index('ix_email_templates_id', table_name='email_templates')
    op.drop_table('email_templates')
    op.drop_table('member_group_members')
    op.drop_index('ix_member_groups_id', table_name='member_groups')
    op.drop_table('member_groups')
