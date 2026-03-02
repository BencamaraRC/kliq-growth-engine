"""Add STAN to Platform enum

Revision ID: b5e8a1d3c702
Revises: a3f2c7e19b04
Create Date: 2026-03-02 18:00:00.000000
"""
from typing import Sequence, Union

from alembic import op


revision: str = "b5e8a1d3c702"
down_revision: Union[str, None] = "a3f2c7e19b04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add STAN to the existing 'platform' enum type in PostgreSQL
    op.execute("ALTER TYPE platform ADD VALUE IF NOT EXISTS 'STAN'")


def downgrade() -> None:
    # PostgreSQL does not support removing values from enums.
    # To fully downgrade, recreate the enum type without STAN.
    pass
