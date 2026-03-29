"""add account_categories table

Revision ID: a1b2c3d4e5f6
Revises: 02e50820f957
Create Date: 2026-03-29 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '02e50820f957'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_SEED = [
    # Income
    ("Dues",          "Income",  "Annual membership dues"),
    ("Show Income",   "Income",  "Revenue from wood-turning shows"),
    ("Store Sale",    "Income",  "Store/merchandise sales"),
    ("Donation",      "Income",  "Charitable donations received"),
    ("Other Income",  "Income",  "Miscellaneous income"),
    # Expense
    ("Venue",         "Expense", "Meeting or event venue costs"),
    ("Supplies",      "Expense", "Club supplies and consumables"),
    ("Program Cost",  "Expense", "Speaker fees and program expenses"),
    ("Printing",      "Expense", "Printing and copying"),
    ("Equipment",     "Expense", "Tools and equipment purchases"),
    ("Website",       "Expense", "Hosting and domain costs"),
    ("Other Expense", "Expense", "Miscellaneous expenses"),
]


def upgrade() -> None:
    op.create_table(
        "account_categories",
        sa.Column("id",          sa.Integer,  primary_key=True),
        sa.Column("name",        sa.String,   nullable=False),
        sa.Column("type",        sa.String,   nullable=False),
        sa.Column("description", sa.String),
        sa.Column("active",      sa.Boolean,  nullable=False, server_default=sa.true()),
    )
    cats = sa.table(
        "account_categories",
        sa.column("name",        sa.String),
        sa.column("type",        sa.String),
        sa.column("description", sa.String),
        sa.column("active",      sa.Boolean),
    )
    op.bulk_insert(cats, [
        {"name": name, "type": typ, "description": desc, "active": True}
        for name, typ, desc in _SEED
    ])


def downgrade() -> None:
    op.drop_table("account_categories")
