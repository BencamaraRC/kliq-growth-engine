"""add onboarding_progress

Revision ID: a3f2c7e19b04
Revises: 8dd1d61b8349
Create Date: 2026-03-02 18:30:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a3f2c7e19b04"
down_revision: Union[str, None] = "8dd1d61b8349"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "onboarding_progress",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("prospect_id", sa.Integer(), nullable=False),
        sa.Column("password_set", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("store_explored", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "content_reviewed", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column(
            "stripe_connected", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("first_share", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("progress_pct", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("started_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["prospect_id"],
            ["prospects.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("prospect_id"),
    )


def downgrade() -> None:
    op.drop_table("onboarding_progress")
