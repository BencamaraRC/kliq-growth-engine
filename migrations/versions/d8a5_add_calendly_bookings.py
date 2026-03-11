"""Add calendly_bookings table and BOOKED_DEMO status

Revision ID: d8a5f3b2e601
Revises: c7f4a2b8d901
Create Date: 2026-03-11 12:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d8a5f3b2e601"
down_revision: Union[str, None] = "c7f4a2b8d901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add BOOKED_DEMO to LinkedIn outreach status enum
    op.execute("ALTER TYPE linkedinoutreachstatus ADD VALUE IF NOT EXISTS 'BOOKED_DEMO'")

    # Create Calendly booking status enum
    op.execute(
        "CREATE TYPE calendlybookingstatus AS ENUM "
        "('SCHEDULED', 'CANCELED', 'COMPLETED')"
    )

    # Create calendly_bookings table
    op.execute("""
        CREATE TABLE calendly_bookings (
            id SERIAL PRIMARY KEY,
            prospect_id INTEGER NOT NULL REFERENCES prospects(id),
            calendly_event_id VARCHAR(255) NOT NULL UNIQUE,
            invitee_email VARCHAR(255) NOT NULL,
            event_type VARCHAR(255),
            scheduled_at TIMESTAMP,
            booked_at TIMESTAMP,
            canceled_at TIMESTAMP,
            status calendlybookingstatus NOT NULL DEFAULT 'SCHEDULED',
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            updated_at TIMESTAMP NOT NULL DEFAULT now()
        )
    """)

    # Index on invitee_email for fast lookup during webhook processing
    op.execute(
        "CREATE INDEX ix_calendly_bookings_invitee_email "
        "ON calendly_bookings (invitee_email)"
    )


def downgrade() -> None:
    op.drop_table("calendly_bookings")
    op.execute("DROP TYPE IF EXISTS calendlybookingstatus")
