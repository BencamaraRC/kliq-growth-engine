"""Add LinkedIn outreach table and prospect columns

Revision ID: c7f4a2b8d901
Revises: b5e8a1d3c702
Create Date: 2026-03-09 12:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c7f4a2b8d901"
down_revision: Union[str, None] = "b5e8a1d3c702"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add LinkedIn columns to prospects
    op.add_column("prospects", sa.Column("linkedin_url", sa.Text(), nullable=True))
    op.add_column(
        "prospects",
        sa.Column("linkedin_found", sa.Boolean(), server_default="false", nullable=False),
    )

    # Create LinkedIn outreach status enum via raw SQL
    op.execute(
        "CREATE TYPE linkedinoutreachstatus AS ENUM "
        "('QUEUED', 'COPIED', 'SENT', 'ACCEPTED', 'DECLINED', 'NO_RESPONSE')"
    )

    # Create linkedin_outreach table
    op.execute("""
        CREATE TABLE linkedin_outreach (
            id SERIAL PRIMARY KEY,
            prospect_id INTEGER NOT NULL UNIQUE REFERENCES prospects(id),
            status linkedinoutreachstatus NOT NULL,
            connection_note TEXT,
            linkedin_url TEXT,
            copied_at TIMESTAMP,
            sent_at TIMESTAMP,
            accepted_at TIMESTAMP,
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            updated_at TIMESTAMP NOT NULL DEFAULT now()
        )
    """)


def downgrade() -> None:
    op.drop_table("linkedin_outreach")
    op.execute("DROP TYPE IF EXISTS linkedinoutreachstatus")
    op.drop_column("prospects", "linkedin_found")
    op.drop_column("prospects", "linkedin_url")
